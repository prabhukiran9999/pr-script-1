#!/usr/bin/env python3

import argparse
import json
import os
import random
import string
from pathlib import Path
from typing import List


def generate_envs(environments: List[str]) -> List[dict]:
    env_names = {
        "dev": "Development",
        "test": "Test",
        "prod": "Production",
        "tools": "Tools",
        "lab": "Lab",
        "sandbox": "Sandbox"
    }

    # Step 1: Define the set of allowed environment names
    allowed_envs = set(env_names.keys())

    # Step 2: Check if provided environment names are valid
    invalid_envs = [env for env in environments if env not in allowed_envs]
    if invalid_envs:
        raise ValueError(f"The following environment names are not allowed: {', '.join(invalid_envs)}. "
                         f"Allowed environment names are: {', '.join(allowed_envs)}.")

    envs = []
    for env in environments:
        envs.append({
            "name": env_names.get(env, env),
            "environment": env
        })
    return envs


def create_or_update_project_spec(projects_path: str, license_plate: str, app_name: str, environments: List[str], admin_email: str, admin_name: str, billing_group: str) -> None:
    project_json_path = os.path.join(projects_path, license_plate, 'project.json')
    if os.path.isfile(project_json_path):
        # Update existing project.json file
        with open(project_json_path, 'r') as project_file:
            project_json = json.load(project_file)
    else:
        # Create new project.json file
        os.makedirs(os.path.join(projects_path, license_plate), exist_ok=True)
        project_json = {"identifier": license_plate}

    # Update fields with specified changes
    if app_name:
        project_json['name'] = app_name
    if environments:
        # Create a mapping of existing environments to their full dictionary representation
        existing_envs = {account["environment"]: account for account in project_json.get("accounts", [])}

        # Generate the dictionary representation of the new environments
        new_envs = generate_envs(environments)

        # Merge the new environments with existing data
        merged_envs = []
        for env in new_envs:
            env_key = env["environment"]
            # If environment exists, update its dictionary with the new data while preserving additional data
            if env_key in existing_envs:
                existing_envs[env_key].update(env)
                merged_envs.append(existing_envs[env_key])
            else:
                merged_envs.append(env)

        # Include existing environments not specified in the 'environments' argument
        for env_key, env in existing_envs.items():
            if env_key not in set(environments):
                merged_envs.append(env)

        # Update the 'accounts' key with the merged environments
        project_json['accounts'] = merged_envs

    # Merge the new tags with existing tags
    existing_tags = project_json.get('tags', {})
    if admin_email:
        existing_tags["admin_contact_email"] = admin_email
    if admin_name:
        existing_tags["admin_contact_name"] = admin_name
    if billing_group:
        existing_tags["billing_group"] = billing_group
    project_json['tags'] = existing_tags

    # Write the updated data back to the file
    with open(project_json_path, 'w') as project_file:
        json.dump(project_json, project_file, indent=2)


def generate_license_plate() -> str:
    return random.choice(string.ascii_lowercase) + ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))


def create_layers(projects_path: str, license_plate: str, layers: List[str], templates_path: str, config_path: str):
    for layer in layers:
        layer_dir = os.path.join(projects_path, license_plate, layer)
        if os.path.exists(layer_dir):
            print(f"WARNING: Layer '{layer_dir}' exists and will NOT be overwritten.")
        else:
            # Determine which template to use for the new layer
            layer_template = os.path.join(templates_path, f"{layer}.hcl.tmpl")
            default_template = os.path.join(templates_path, "default_layer.hcl.tmpl")
            if os.path.isfile(os.path.join(config_path, f"{layer}.hcl")):
                print(f"Layer '{layer_dir}' does not exist and will be created.")
                os.makedirs(layer_dir, exist_ok=True)

                template = layer_template if os.path.isfile(layer_template) else default_template
                print(f"Layer '{layer}' will be created using the template at '{template}'.")

                # Read the contents of the template file
                with open(template, 'r') as template_file:
                    template_str = template_file.read()

                # Render the template with the layer name
                template_obj = string.Template(template_str)
                rendered_template = template_obj.substitute(layer=layer)

                # Write the rendered template to the new layer's terragrunt.hcl file
                with open(os.path.join(layer_dir, 'terragrunt.hcl'), 'w') as layer_file:
                    layer_file.write(rendered_template)
            else:
                print(f"WARNING: Layer '{layer}' is not a valid layer and cannot be created.")


def comma_separated_values(value_str):
    return value_str.split(',')


def flatten(nested_list):
    return [item for sublist in nested_list for item in sublist]


def main():
    parser = argparse.ArgumentParser(description='Create or update project specification.')
    parser.add_argument('-lp', '--license_plate', type=str, help='Existing or externally generated license_plate.')
    parser.add_argument('-e', '--env', type=comma_separated_values, action='append', default=[], help='Comma-separated environment names or use multiple times (e.g., -e dev,test or -e dev -e test).')
    parser.add_argument('-l', '--layer', type=comma_separated_values, action='append', default=[], help='Terraform module layers. A layer is valid if it has a corresponding \'layer.hcl\' file in the config (terragrunt) directory. You can specify multiple layers either by separating them with commas or by using the flag multiple times (e.g., -l layer1,layer2 or -l layer1 -l layer2).')
    parser.add_argument('-pn', '--project_name', type=str, help='Name of the teams project.')
    parser.add_argument('-ae', '--admin_email', type=str, help='Main contact for the project (email for billing reports).')
    parser.add_argument('-an', '--admin_name', type=str, help='Name of the main contact for the project.')
    parser.add_argument('-bg', '--billing_group', type=str, help='Name of the billing group.')
    args = parser.parse_args()

    args.env = flatten(args.env)
    args.layer = flatten(args.layer)

    # Get the current working directory as a pathlib.Path object
    cwd = Path.cwd()

    # Construct the required paths using the / operator for path joining
    projects_path = cwd / '..' / '..' / 'projects'
    templates_path = cwd / '..' / '..' / 'templates'
    config_path = cwd / '..' / 'terragrunt'

    # Resolve the paths to their absolute forms
    projects_path = projects_path.resolve()
    templates_path = templates_path.resolve()
    config_path = config_path.resolve()

    # Generate license plate if not provided
    license_plate = args.license_plate if args.license_plate else generate_license_plate()

    create_or_update_project_spec(projects_path, license_plate, args.project_name, args.env, args.admin_email, args.admin_name, args.billing_group)

    # Create or update layers
    create_layers(projects_path, license_plate, args.layer, templates_path, config_path)


if __name__ == "__main__":
    main()