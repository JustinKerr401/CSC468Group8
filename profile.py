import geni.portal as portal
import geni.rspec.pg as rspec

# Create a Request object to start building the RSpec.
request = portal.context.makeRequestRSpec()

# Create a XenVM
node = request.XenVM("node")
node.disk_image = "urn:publicid:IDN+emulab.net+image+emulab-ops:UBUNTU22-64-STD"
node.routable_control_ip = "true"

# Update packages and install git and apache2
node.addService(rspec.Execute(shell="/bin/sh", command="sudo apt update"))
node.addService(rspec.Execute(shell="/bin/sh", command="sudo apt install -y apache2 git"))

# Clone your GitHub repo
node.addService(rspec.Execute(shell="/bin/sh", command="git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git"))

# Optionally, start apache2 service
node.addService(rspec.Execute(shell="/bin/sh", command="sudo systemctl start apache2"))
node.addService(rspec.Execute(shell="/bin/sh", command="sudo systemctl status apache2"))

# Print the RSpec to the enclosing page
portal.context.printRequestRSpec()
