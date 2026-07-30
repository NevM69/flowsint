from typing import Any, Dict, List, Optional

from flowsint_core.core.enricher_base import Enricher
from flowsint_core.core.logger import Logger
from flowsint_enrichers.registry import flowsint_enricher
from flowsint_types.address import Location
from flowsint_types.individual import Individual
from flowsint_types.organization import Organization
from tools.organizations.pappers import PappersTool


@flowsint_enricher
class OrgToPappersEnricher(Enricher):
    """[Pappers] Enrich an Organization with legal, financial, and beneficial ownership data (France only)."""

    InputType = Organization
    OutputType = Organization

    def __init__(
        self,
        sketch_id: Optional[str] = None,
        scan_id: Optional[str] = None,
        vault=None,
        params: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            sketch_id=sketch_id,
            scan_id=scan_id,
            params_schema=self.get_params_schema(),
            vault=vault,
            params=params,
        )
        # scan() collects beneficial owners here (Organization has no dedicated field for
        # them), keyed by SIREN, so postprocess can attach them as graph relationships.
        self._beneficiaires_by_siren: Dict[str, List[Individual]] = {}

    @classmethod
    def get_params_schema(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "PAPPERS_API_KEY",  # Get your API token from https://www.pappers.fr/api
                "type": "vaultSecret",
                "description": "Your Pappers API token.",
                "required": True,
            }
        ]

    @classmethod
    def name(cls) -> str:
        return "org_to_pappers"

    @classmethod
    def category(cls) -> str:
        return "Organization"

    @classmethod
    def key(cls) -> str:
        return "siren"

    async def scan(self, data: List[InputType]) -> List[OutputType]:
        results: List[OutputType] = []
        api_token = self.get_secret("PAPPERS_API_KEY")
        pappers = PappersTool(api_token=api_token)

        for org in data:
            try:
                siren = org.siren
                if not siren:
                    matches = pappers.search_entreprise(org.name, limit=1)
                    if not matches:
                        Logger.error(
                            self.sketch_id,
                            {
                                "message": f"(OrgToPappersEnricher) No Pappers match for '{org.name}'."
                            },
                        )
                        continue
                    siren = matches[0].get("siren")
                    if not siren:
                        continue

                company = pappers.get_entreprise(siren)
                enriched = self.enrich_org(org, company)
                if enriched is not None:
                    results.append(enriched)
            except Exception as e:
                Logger.error(
                    self.sketch_id,
                    {
                        "message": f"(OrgToPappersEnricher) Error enriching organization '{org.name}': {e}"
                    },
                )

        return results

    def enrich_org(
        self, org: Organization, company: Dict[str, Any]
    ) -> Optional[Organization]:
        # Mutate a copy of the existing organization instead of building a fresh one:
        # unset fields are skipped so we don't null out data set by other enrichers
        # (Neo4j's `SET n += props` removes a property when the incoming value is null).
        enriched = org.model_copy(deep=True)

        siren = company.get("siren")
        if siren:
            enriched.siren = siren

        name = company.get("nom_entreprise") or company.get("denomination")
        if name:
            enriched.name = name
            enriched.nom_complet = name
        if company.get("denomination"):
            enriched.nom_raison_sociale = company.get("denomination")
        if company.get("sigle"):
            enriched.sigle = company.get("sigle")

        if company.get("forme_juridique"):
            enriched.nature_juridique = company.get("forme_juridique")
        if company.get("categorie_entreprise"):
            enriched.categorie_entreprise = company.get("categorie_entreprise")
        if company.get("annee_categorie_entreprise"):
            enriched.annee_categorie_entreprise = company.get(
                "annee_categorie_entreprise"
            )
        if company.get("tranche_effectif"):
            enriched.tranche_effectif_salarie = company.get("tranche_effectif")
        if company.get("annee_effectif"):
            enriched.annee_tranche_effectif_salarie = company.get("annee_effectif")
        if company.get("code_naf"):
            enriched.activite_principale = company.get("code_naf")
        if company.get("libelle_code_naf"):
            enriched.section_activite_principale = company.get("libelle_code_naf")
        if company.get("date_creation"):
            enriched.date_creation = company.get("date_creation")
        if company.get("date_cessation"):
            enriched.date_fermeture = company.get("date_cessation")
        if company.get("finances"):
            enriched.finances = company.get("finances")

        siege = company.get("siege") or {}
        if siege.get("siret"):
            enriched.siege_siret = siege.get("siret")
        if siege.get("adresse_ligne_1"):
            enriched.siege_adresse = siege.get("adresse_ligne_1")
        if siege.get("code_postal"):
            enriched.siege_code_postal = siege.get("code_postal")
        if siege.get("ville"):
            enriched.siege_libelle_commune = siege.get("ville")
        if siege.get("latitude"):
            enriched.siege_latitude = siege.get("latitude")
        if siege.get("longitude"):
            enriched.siege_longitude = siege.get("longitude")
        if siege.get("latitude") and siege.get("longitude"):
            enriched.siege_geo_adresse = Location(
                address=siege.get("adresse_ligne_1", ""),
                city=siege.get("ville", ""),
                country="FR",
                zip=siege.get("code_postal", ""),
                latitude=float(siege.get("latitude")),
                longitude=float(siege.get("longitude")),
            )

        # Leaders (representants)
        dirigeants = []
        for rep in company.get("representants") or []:
            try:
                is_morale = rep.get("type_dirigeant") == "morale"
                full_name = (
                    rep.get("denomination")
                    if is_morale
                    else f"{rep.get('prenom', '')} {rep.get('nom', '')}".strip()
                )
                if not full_name:
                    continue
                dirigeants.append(
                    Individual(
                        full_name=full_name,
                        first_name=rep.get("prenom") if not is_morale else None,
                        last_name=rep.get("nom") if not is_morale else None,
                        birth_date=rep.get("date_de_naissance"),
                        nationality=rep.get("nationalite"),
                        job_title=rep.get("qualite"),
                        source="Pappers",
                    )
                )
            except Exception as e:
                Logger.error(
                    self.sketch_id,
                    {
                        "message": f"(OrgToPappersEnricher) Skipping malformed representant: {e}"
                    },
                )
        if dirigeants:
            enriched.dirigeants = dirigeants

        # Beneficial owners - not an Organization field, stashed for postprocess.
        beneficiaires = []
        for beneficiaire in company.get("beneficiaires_effectifs") or []:
            try:
                full_name = f"{beneficiaire.get('prenom', '')} {beneficiaire.get('nom', '')}".strip()
                if not full_name:
                    continue
                pct_parts = beneficiaire.get("pourcentage_parts")
                pct_votes = beneficiaire.get("pourcentage_votes")
                note_parts = []
                if pct_parts is not None:
                    note_parts.append(f"{pct_parts}% des parts")
                if pct_votes is not None:
                    note_parts.append(f"{pct_votes}% des votes")
                beneficiaires.append(
                    Individual(
                        full_name=full_name,
                        first_name=beneficiaire.get("prenom"),
                        last_name=beneficiaire.get("nom"),
                        birth_date=beneficiaire.get("date_de_naissance_formate"),
                        nationality=beneficiaire.get("nationalite"),
                        notes=(
                            f"Bénéficiaire effectif ({', '.join(note_parts)})"
                            if note_parts
                            else "Bénéficiaire effectif"
                        ),
                        source="Pappers",
                    )
                )
            except Exception as e:
                Logger.error(
                    self.sketch_id,
                    {
                        "message": f"(OrgToPappersEnricher) Skipping malformed beneficiaire effectif: {e}"
                    },
                )
        if beneficiaires and enriched.siren:
            self._beneficiaires_by_siren[enriched.siren] = beneficiaires

        return enriched

    def postprocess(
        self, results: List[OutputType], input_data: List[InputType]
    ) -> List[OutputType]:
        if not self._graph_service:
            return results

        for org in results:
            self.create_node(org)

            if org.dirigeants:
                for dirigeant in org.dirigeants:
                    self.create_node(dirigeant)
                    self.create_relationship(org, dirigeant, "HAS_LEADER")
                    self.log_graph_message(
                        f"{org.name}: HAS_LEADER -> {dirigeant.full_name}"
                    )

            if org.siege_geo_adresse:
                self.create_node(org.siege_geo_adresse)
                self.create_relationship(org, org.siege_geo_adresse, "HAS_ADDRESS")
                self.log_graph_message(
                    f"{org.name}: HAS_ADDRESS -> {org.siege_geo_adresse.address}, {org.siege_geo_adresse.city}"
                )

            for beneficiaire in self._beneficiaires_by_siren.get(org.siren or "", []):
                self.create_node(beneficiaire)
                self.create_relationship(org, beneficiaire, "HAS_BENEFICIAL_OWNER")
                self.log_graph_message(
                    f"{org.name}: HAS_BENEFICIAL_OWNER -> {beneficiaire.full_name}"
                )

        return results


InputType = OrgToPappersEnricher.InputType
OutputType = OrgToPappersEnricher.OutputType
