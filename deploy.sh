rsync -avz custom_components/ha_nostr_bridge root@homeassistant.local:/root/config/custom_components
echo "      RESTARTING HOME ASSISTANT"
echo "======================================"
echo "Please wait, this may take a minute..."
ssh root@homeassistant.local "ha core restart"
echo "Done!"
