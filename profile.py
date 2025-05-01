import geni.portal as portal
import geni.rspec.pg as rspec

# Create a Request object to start building the RSpec.
request = portal.context.makeRequestRSpec()

# Create a XenVM
node = request.XenVM("node")
node.disk_image = "urn:publicid:IDN+emulab.net+image+emulab-ops:UBUNTU22-64-STD"
node.routable_control_ip = "true"

# Update system and install necessary packages
node.addService(rspec.Execute(shell="/bin/sh", command="sudo apt update -y"))
node.addService(rspec.Execute(shell="/bin/sh", command="sudo DEBIAN_FRONTEND=noninteractive apt install -y apache2 git curl"))

# Install Docker
node.addService(rspec.Execute(shell="/bin/sh", command="curl -fsSL https://get.docker.com -o get-docker.sh"))
node.addService(rspec.Execute(shell="/bin/sh", command="sudo sh get-docker.sh"))
node.addService(rspec.Execute(shell="/bin/sh", command="sudo usermod -aG docker $(whoami)"))

# Install Docker Compose v2 manually
node.addService(rspec.Execute(
    shell="/bin/sh",
    command=(
        "sudo curl -L \"https://github.com/docker/compose/releases/download/v2.23.3/"
        "docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose"
    )
))
node.addService(rspec.Execute(shell="/bin/sh", command="sudo chmod +x /usr/local/bin/docker-compose"))

# Create target directory and clone the GitHub repository
node.addService(rspec.Execute(shell="/bin/sh", command="mkdir -p /home/Stock-Trader-Aider"))
node.addService(rspec.Execute(
    shell="/bin/sh",
    command="git clone --branch main https://github.com/JustinKerr401/Stock-Trader-Aider.git /home/Stock-Trader-Aider"
))

# Start apache2
node.addService(rspec.Execute(shell="/bin/sh", command="sudo systemctl start apache2"))
node.addService(rspec.Execute(shell="/bin/sh", command="sudo systemctl status apache2"))

# Print the RSpec to the enclosing page
portal.context.printRequestRSpec()
