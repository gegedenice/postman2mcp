# my_mcp_tool/cli.py
import click
from .postman_harvester import harvest_postman_collection
from .openapi_converter import convert_to_openapi
from .file_generator import generate_project_files
import os

@click.command()
@click.option('--collection-id', required=True, help='Postman collection ID')
@click.option('--project-dir', default='my-mcp-project', help='Directory to create the project in')
@click.option('--postman-api-key', required=True, help='Postman API key')
@click.option('--ngrok-authtoken', required=False, help='Ngrok authentication token')
def main(collection_id, project_dir, postman_api_key, ngrok_authtoken):
    # Ensure the project directory exists
    project_dir = os.path.abspath(project_dir)
    if not os.path.exists(project_dir):
        os.makedirs(project_dir)
    # Step 1: Harvest Postman collection
    postman_collection = harvest_postman_collection(collection_id, postman_api_key)

    # Step 2: Convert to OpenAPI
    openapi_spec, base_url = convert_to_openapi(postman_collection)

    # Step 3: Generate project files
    generate_project_files(project_dir, postman_collection, openapi_spec, base_url, postman_api_key, ngrok_authtoken=None)
    click.echo(f"Project files generated in {project_dir}")

if __name__ == '__main__':
    main()