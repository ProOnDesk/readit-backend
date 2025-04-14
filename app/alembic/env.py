from logging.config import fileConfig
import alembic.operations
from sqlalchemy import engine_from_config, pool, text, sql
from alembic import context
from app.domain.model_base import Base
from alembic.operations.ops import DropColumnOp, AddColumnOp, ModifyTableOps, ExecuteSQLOp
import alembic
import logging

# Alembic Config object
config = context.config

# # Logging configuration
# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Custom logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('alembic.custom')

def process_revision_directives(context, revision, directives):
    """
    Custom hook to modify auto-generated migration scripts.
    """
    script: alembic.operations.ops.MigrationScript = directives[0]
    
    print('\n')
    upo: alembic.operations.ops.UpgradeOps = script.upgrade_ops

    # To prevent infinite loop, track modified columns
    processed_columns = set()

    for op_list in upo.ops:
        i = 0
        for op in op_list.ops:
            if isinstance(op, AddColumnOp):
                addcolumnop: AddColumnOp = op
                column = addcolumnop.column

                if not column.nullable and (addcolumnop.table_name, column.name) not in processed_columns:
                    print(f"Handling non-nullable column: {column.name}")
                    column.nullable = True
                    # Mark this column as processed
                    processed_columns.add((addcolumnop.table_name, column.name))

                    # Add column as nullable
                    op_list.ops.insert(
                        i,  
                        AddColumnOp(
                            table_name=addcolumnop.table_name,
                            column=column.copy(),
                            schema=None
                        )
                    )
                    i += 1

                    # Update existing rows to set a default value
                    print(column.type)
                    column_default = ''
                    if str(column.type) in ["INTEGER", "FLOAT"]:
                        column_default = 0
                    if str(column.type) in ["BOOLEAN"]:
                        column_default = False
                    if str(column.type) in ["DATETIME"]:
                        column_default = sql.func.now()

                    op_list.ops.insert(
                        i,
                        alembic.operations.ops.ExecuteSQLOp(
                            sqltext=f"UPDATE {addcolumnop.table_name} SET {column.name} = '{column_default}' WHERE {column.name} IS NULL"
                        )
                    )

                    i += 1

                    # Alter column to be non-nullable
                    op_list.ops.insert(
                        i,
                        alembic.operations.ops.AlterColumnOp(
                            table_name=addcolumnop.table_name,
                            column_name=column.name,
                            existing_type=column.type,
                            nullable=False
                        )
                    )

                    i += 1

                    op_list.ops.pop(i)

                    # Reset column properties
                    column.nullable = False
                else:
                    i += 1

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
