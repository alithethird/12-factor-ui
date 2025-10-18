# Version key/value should be on his own line
PACKAGE_VERSION=$(cat rockcraft.yaml \
  | grep version \
  | head -1 \
  | awk -F: '{ print $2 }' \
  | sed 's/[",]//g')
PACKAGE_VERSION=${PACKAGE_VERSION%#*}

echo $PACKAGE_VERSION


version=$(grep '^version:' "rockcraft.yaml" | cut -d'"' -f2)

echo "Version: ### $version ###"

rockname=$(grep '^name:' "rockcraft.yaml" | cut -d':' -f2 | xargs)
echo "Rock Name: ### $rockname ###"

