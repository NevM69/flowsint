from flowsint_enrichers.organization.to_pappers import OrgToPappersEnricher
from flowsint_types.organization import Organization

PAPPERS_COMPANY = {
    "siren": "552032534",
    "nom_entreprise": "EXAMPLE SA",
    "denomination": "EXAMPLE SA",
    "forme_juridique": "SA à conseil d'administration",
    "categorie_entreprise": "GE",
    "annee_categorie_entreprise": 2023,
    "tranche_effectif": "53",
    "annee_effectif": 2023,
    "code_naf": "62.01Z",
    "libelle_code_naf": "Programmation informatique",
    "date_creation": "1970-01-01",
    "finances": {"2023": {"chiffre_affaires": 1000000}},
    "siege": {
        "siret": "55203253400015",
        "adresse_ligne_1": "1 RUE EXEMPLE",
        "code_postal": "75001",
        "ville": "PARIS",
        "latitude": "48.8566",
        "longitude": "2.3522",
    },
    "representants": [
        {
            "type_dirigeant": "physique",
            "nom": "DUPONT",
            "prenom": "Jean",
            "qualite": "Président",
            "date_de_naissance": "1970-01",
            "nationalite": "Française",
        }
    ],
    "beneficiaires_effectifs": [
        {
            "nom": "DUPONT",
            "prenom": "Jean",
            "date_de_naissance_formate": "01/1970",
            "nationalite": "Française",
            "pourcentage_parts": 60,
            "pourcentage_votes": 60,
        }
    ],
}


def make_enricher() -> OrgToPappersEnricher:
    return OrgToPappersEnricher(sketch_id="test-sketch", scan_id="test-scan")


def test_name_category_key():
    enricher = make_enricher()
    assert enricher.name() == "org_to_pappers"
    assert enricher.category() == "Organization"
    assert enricher.key() == "siren"


def test_enrich_org_maps_identity_and_financial_fields():
    enricher = make_enricher()
    org = Organization(name="Example")

    enriched = enricher.enrich_org(org, PAPPERS_COMPANY)

    assert enriched.siren == "552032534"
    assert enriched.name == "EXAMPLE SA"
    assert enriched.nature_juridique == "SA à conseil d'administration"
    assert enriched.tranche_effectif_salarie == "53"
    assert enriched.activite_principale == "62.01Z"
    assert enriched.finances == {"2023": {"chiffre_affaires": 1000000}}


def test_enrich_org_maps_siege_address():
    enricher = make_enricher()
    org = Organization(name="Example")

    enriched = enricher.enrich_org(org, PAPPERS_COMPANY)

    assert enriched.siege_siret == "55203253400015"
    assert enriched.siege_libelle_commune == "PARIS"
    assert enriched.siege_geo_adresse is not None
    assert enriched.siege_geo_adresse.city == "PARIS"


def test_enrich_org_maps_dirigeants():
    enricher = make_enricher()
    org = Organization(name="Example")

    enriched = enricher.enrich_org(org, PAPPERS_COMPANY)

    assert enriched.dirigeants is not None
    assert len(enriched.dirigeants) == 1
    assert enriched.dirigeants[0].full_name == "Jean DUPONT"
    assert enriched.dirigeants[0].job_title == "Président"


def test_enrich_org_stashes_beneficiaires_effectifs_by_siren():
    enricher = make_enricher()
    org = Organization(name="Example")

    enriched = enricher.enrich_org(org, PAPPERS_COMPANY)

    beneficiaires = enricher._beneficiaires_by_siren.get(enriched.siren)
    assert beneficiaires is not None
    assert len(beneficiaires) == 1
    assert beneficiaires[0].full_name == "Jean DUPONT"
    assert "60% des parts" in beneficiaires[0].notes


def test_enrich_org_preserves_existing_fields_not_returned_by_pappers():
    enricher = make_enricher()
    org = Organization(name="Example", siren="552032534", sigle="EX")

    enriched = enricher.enrich_org(org, {"siren": "552032534"})

    # Pappers response had no `sigle`, so the pre-existing value must survive
    # (a fresh, mostly-None Organization would null it out via Neo4j's `SET n += props`).
    assert enriched.sigle == "EX"
