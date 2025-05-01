import geni.portal as portal
import geni.rspec.pg as rspec

# Create a Request object to start building the RSpec.
request = portal.context.makeRequestRSpec()

# Create a XenVM
node = request.XenVM("node")
node.disk_image = "urn:publicid:IDN+emulab.net+image+emulab-ops:UBUNTU22-64-STD"
node.routable_control_ip = "true"

# Update packages and install git, apache2, docker, and docker-compose
node.addService(rspec.Execute(shell="/bin/sh", command="sudo apt update -y"))
node.addService(rspec.Execute(shell="/bin/sh", command="sudo DEBIAN_FRONTEND=noninteractive apt install -y apache2 git docker.io docker-compose"))

# Enable and start Docker
node.addService(rspec.Execute(shell="/bin/sh", command="sudo systemctl enable docker"))
node.addService(rspec.Execute(shell="/bin/sh", command="sudo systemctl start docker"))

# Optionally: Start apache2 service
node.addService(rspec.Execute(shell="/bin/sh", command="sudo systemctl start apache2"))

# (Optional) Check service status - mainly for debugging
node.addService(rspec.Execute(shell="/bin/sh", command="sudo systemctl status apache2"))
node.addService(rspec.Execute(shell="/bin/sh", command="sudo systemctl status docker"))

# Print the RSpec to the enclosing page
portal.context.printRequestRSpec()
