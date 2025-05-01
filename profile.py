import geni.portal as portal
import geni.rspec.pg as rspec

# Create a Request object to start building the RSpec.
request = portal.context.makeRequestRSpec()

# Create a XenVM
node = request.XenVM("node")
node.disk_image = "urn:publicid:IDN+emulab.net+image+emulab-ops:UBUNTU22-64-STD"
node.routable_control_ip = "true"

# Update packages and install git, curl, apache2
node.addService(rspec.Execute(shell="/bin/sh", command="sudo apt update -y"))
node.addService(rspec.Execute(shell="/bin/sh", command="sudo DEBIAN_FRONTEND=noninteractive apt install -y git curl apache2"))

# Install Docker
node.addService(rspec.Execute(shell="/bin/sh", command="curl -fsSL https://get.docker.com -o get-docker.sh"))
node.addService(rspec.Execute(shell="/bin/sh", command="sudo sh get-docker.sh"))
node.addService(rspec.Execute(shell="/bin/sh", command="sudo usermod -aG docker $(whoami)"))

# Install Docker Compose v2
node.addService(rspec.Execute(
    shell="/bin/sh",
    command=(
        "sudo curl -L \"https://github.com/docker/compose/releases/download/v2.23.3/"
        "docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose"
    )
))
node.addService(rspec.Execute(shell="/bin/sh", command="sudo chmod +x /usr/local/bin/docker-compose"))

# Clone GitHub repository into a public directory (not just ~ or root)
node.addService(rspec.Execute(shell="/bin/sh", command="sudo mkdir -p /home/Stock-Trader-Aider"))
node.addService(rspec.Execute(shell="/bin/sh", command="sudo git clone --branch main https://github.com/JustinKerr401/Stock-Trader-Aider.git /home/Stock-Trader-Aider"))
node.addService(rspec.Execute(shell="/bin/sh", command="sudo chown -R $(whoami):$(whoami) /home/Stock-Trader-Aider"))

# Start apache2
node.addService(rspec.Execute(shell="/bin/sh", command="sudo systemctl start apache2"))
node.addService(rspec.Execute(shell="/bin/sh", command="sudo systemctl status apache2"))

# Print the RSpec to the enclosing page
portal.context.printRequestRSpec()
