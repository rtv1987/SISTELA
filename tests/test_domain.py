from decimal import Decimal

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.orm import Session

from sistela.db import make_engine, migrate
from sistela.models import EstimateLine, EstimateSection, Project


@pytest.fixture
def engine(tmp_path):
    migrate(tmp_path)
    result = make_engine(tmp_path)
    yield result
    result.dispose()


def test_migration_is_repeatable_and_complete(engine, tmp_path):
    migrate(tmp_path)
    assert set(inspect(engine).get_table_names()) == {
        "alembic_version",
        "projects",
        "source_documents",
        "estimate_sections",
        "estimate_lines",
        "sistela_mappings",
        "import_runs",
        "requirements",
        "grid_changes", "mapping_confirmations",
        "historical_imports", "historical_estimates", "historical_lines", "historical_reviews",
    }


def test_exact_decimal_and_independent_descriptions(engine):
    with Session(engine) as session:
        project = Project(name="GSS", system_type="GSS")
        session.add(project)
        session.flush()
        line = EstimateLine(
            project_id=project.id,
            project_description="Detektorių montavimas",
            output_description="Projekto tekstas",
            sistela_code="USER-CODE",
            sistela_original_description="Originalas",
            quantity=Decimal("123456789012345.123456"),
            work_price=Decimal("0.100001"),
        )
        session.add(line)
        session.commit()
        session.expire_all()
        loaded = session.scalars(select(EstimateLine)).one()
        assert loaded.quantity == Decimal("123456789012345.123456")
        assert loaded.work_price == Decimal("0.100001")
        assert (
            session.execute(text("SELECT typeof(quantity) FROM estimate_lines")).scalar() == "text"
        )
        loaded.sistela_code = "CHANGED-CODE"
        session.commit()
        assert loaded.output_description == "Projekto tekstas"
        assert loaded.project_description == "Detektorių montavimas"
        assert loaded.sistela_original_description == "Originalas"


def test_cross_project_section_rejected(engine):
    with Session(engine) as session:
        one, two = Project(name="One", system_type="GSS"), Project(name="Two", system_type="GSS")
        session.add_all([one, two])
        session.flush()
        section = EstimateSection(project_id=one.id, name="Medžiagos")
        session.add(section)
        session.flush()
        session.add(
            EstimateLine(
                project_id=two.id,
                section_id=section.id,
                project_description="X",
                output_description="X",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_float_rejected_at_storage_boundary(engine):
    with Session(engine) as session:
        p = Project(name="P", system_type="GSS")
        session.add(p)
        session.flush()
        session.add(
            EstimateLine(
                project_id=p.id, project_description="X", output_description="X", quantity=0.1
            )
        )
        with pytest.raises(StatementError, match="not float"):
            session.commit()


def test_upgrade_preserves_legacy_mapping_and_count_constraint(tmp_path):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import MetaData, Table

    from sistela.db import ROOT, database_url

    config = Config(str(ROOT / 'alembic.ini'))
    config.set_main_option('script_location', str(ROOT / 'backend/migrations'))
    config.set_main_option('sqlalchemy.url', database_url(tmp_path).render_as_string().replace('%', '%%'))
    command.upgrade(config, '231609db4375')
    engine = make_engine(tmp_path)
    table = Table('sistela_mappings', MetaData(), autoload_with=engine)
    with engine.begin() as connection:
        connection.execute(table.insert().values(id='legacy', system_type='GSS', source_text='Cable',
            normalized_source_text='cable', sistela_code='TEST', sistela_description='Historical text',
            usage_count=2, confirmed_count=1, created_at='2026-01-01', updated_at='2026-01-01'))
    command.upgrade(config, 'head')
    command.check(config)
    with engine.connect() as connection:
        row = connection.execute(text('SELECT * FROM sistela_mappings')).mappings().one()
        assert row['source_unit'] == '' and row['confirmed_count'] == 1
        assert row['sistela_description'] == 'Historical text'
        with pytest.raises(IntegrityError):
            connection.execute(text('UPDATE sistela_mappings SET confirmed_count = -1'))
    engine.dispose()
