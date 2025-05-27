import click
from sql_manager import PostgreSQLManager

@click.group()
def cli():
    """Утилита для работы с PostgreSQL (мастер + реплика)"""
    pass

@cli.command()
@click.option('--replica', is_flag=True, help='Использовать реплику вместо мастера')
@click.argument('script_path', type=click.Path(exists=True))
def run_script(script_path: str, replica: bool):
    """Выполнить SQL скрипт из файла"""
    db = PostgreSQLManager()
    db.execute_script(script_path, use_replica=replica)

@cli.command()
@click.option('--replica', is_flag=True, help='Использовать реплику вместо мастера')
@click.argument('query')
def run_query(query: str, replica: bool):
    """Выполнить SQL запрос"""
    db = PostgreSQLManager()
    result = db.execute_query(query, use_replica=replica, fetch=True)
    click.echo("Query result:")
    click.echo(result)

if __name__ == "__main__":
    cli()
