#!/bin/bash

usage() {
	echo "$0 help"
	echo "$0 [-lp|--license_plate <existing or externally generated license_plate>] [-e|--env <dev|test|prod|sandbox>]...* [-l|--layer <valid layer name>]...
		[-pn | --project_name <name of the teams project>] [-ae | --admin_email <main contact for the project, this is the email that the billing reports will be sent to>]
		[-an | --admin_name <name of the main contact for the project>] [-bg | --billing_group <name of the billing group>]"
	echo "    - If no license_plate is provided, one will be generated."
	echo "    - If no layers specified, only the project spec will be created."
	echo "    - Valid layers are named after the .hcl files in the projects directory. e.g. 'accounts', 'alb', 'automation', etc."
	echo "    - Giving different project sets the same billing group will group them together for the billing report emails.
		This use case might be for executives funding multiple projects on the platform."
	exit 0
}


apply_template() {
	(
		trap 'rm -f $tempfile' EXIT
		tempfile=$(mktemp $(pwd)/templateXXXXXX)

		echo 'cat <<END_TEMPLATE' >$tempfile
		cat $1 >>$tempfile
		echo END_TEMPLATE >>$tempfile

		. $tempfile
	)
}

dev="Development"
test="Test"
prod="Production"
tools="Tools"
lab="Lab"
sandbox="Sandbox"

generate_envs() {
	## how many envs
	len=${#environments[@]}

	## Use bash for loop
	for ((i = 0; i < $len; i++)); do
		env="${environments[$i]}"
		cat <<EOF
	{
      "name": "${!env}",
      "environment": "${env}"
    } $( let next_num=i+1; if [ $next_num -eq $len ]; then echo ""; else echo ","; fi )
EOF
	done
}

create_project_spec() {

	mkdir -p ${projects_path}/$license_plate

	cat <<EOF >${projects_path}/$license_plate/project.json
{
  "identifier": "${license_plate}",
  "name": "${app_name}",
  "accounts": [
    $(generate_envs)
  ],
  "tags": {
    "admin_contact_email": "${admin_email}",
    "admin_contact_name": "${admin_name}",
    "billing_group": "${billing_group}"
  }
}

EOF

}

projects_path="../../projects"
templates_path="../../templates"
config_path="../terragrunt"
layers=()
environments=()

#process inputs
while [ "$1" != "" ]; do
	case $1 in
	-l | --layer)
		shift
		layers+=("$1")
		;;
	-lp | --license_plate)
		shift
		license_plate="$1"
		;;
	-pn | --project_name)
		shift
		app_name="$1"
		;;
	-e | --env)
		shift
		environments+=("$1")
		;;
	-ae | --admin_email)
		shift
		admin_email="$1"
		;;
	-an | --admin_name)
		shift
		admin_name="$1"
		;;
	-bg | --billing_group)
		shift
		billing_group="$1"
		;;
	-h | --help)
		usage
		exit
		;;
	*)
		usage
		exit 1
		;;
	esac
	shift
done

if [ -z "$license_plate" ]; then
	license_plate=$(cat <(LC_ALL=C tr -dc a-z </dev/urandom | head -c 1) <(LC_ALL=C tr -dc a-z0-9 </dev/urandom | head -c 5) <(echo))
fi

if [ -f "${projects_path}/$license_plate/project.json" ]; then
	echo "Project set with license plate: '$license_plate' already exists."
else
	echo "Creating new project set with license plate: '$license_plate'..."
	create_project_spec
fi

for layer in "${layers[@]}"; do
	if [ -f "${templates_path}/${layer}.hcl.tmpl" ] || [ -f "${config_path}/${layer}.hcl" ]; then
		if [ -d "${projects_path}/$license_plate/$layer" ]; then
			echo "WARNING: Layer  '${projects_path}/$license_plate/${layer}' exists and will NOT be overwritten."
		else
			echo "Layer  '${projects_path}/$license_plate/${layer}' does not exist and will be created."

			# create the path for the new layer
			mkdir -p ${projects_path}/$license_plate/${layer}

			# determine which template to use for the new layer
			if [ -f "${templates_path}/${layer}.hcl.tmpl" ]; then
				template="${templates_path}/${layer}.hcl.tmpl"
			else
				template="${templates_path}/default_layer.hcl.tmpl"
			fi

			# create the new layer using the selected template and write it to the correct place
			echo "Layer '${layer}' will be created using the template at '$template'."
			apply_template "$template" >${projects_path}/${license_plate}/${layer}/terragrunt.hcl
		fi
	else
		echo "WARNING: Layer '$layer' is not a valid layer and cannot be created."
	fi
done
