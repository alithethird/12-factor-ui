#!/bin/bash

version=$(grep '^version:' "rockcraft.yaml" | cut -d'"' -f2)

modelname=baremodel
appname=bareapp
rockname=$(grep '^name:' "rockcraft.yaml" | cut -d':' -f2 | xargs)
charmname=$(grep '^name:' "charm/charmcraft.yaml" | cut -d':' -f2 | xargs)

juju ssh --container=app $appname/0 pebble exec bash
juju ssh --container=app $appname/0 pebble plan
juju ssh --container=app $appname/0 pebble -h
