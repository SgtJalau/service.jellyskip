#!/bin/bash
COREELEC_IP="192.168.86.180"

echo "🚀 Deploying JellySkip to CoreELEC..."

# Syntax check Python files first
echo "🔍 Checking Python syntax..."
for file in resources/lib/*.py; do
    if [[ -f "$file" ]]; then
        python3 -m py_compile "$file"
        if [[ $? -ne 0 ]]; then
            echo "❌ Syntax error in $file"
            exit 1
        fi
    fi
done
echo "✅ Python syntax check passed"

# Verify SSH key authentication
if ! ssh -o BatchMode=yes root@$COREELEC_IP "echo 'SSH OK'" >/dev/null 2>&1; then
    echo "❌ SSH key authentication failed. Run: ssh-copy-id root@$COREELEC_IP"
    exit 1
fi

# Deploy addon
echo "📂 Deploying addon..."
ssh root@$COREELEC_IP "rm -rf /storage/.kodi/addons/service.jellyskip"
scp -r . root@$COREELEC_IP:/storage/.kodi/addons/service.jellyskip
ssh root@$COREELEC_IP "chmod -R 755 /storage/.kodi/addons/service.jellyskip"

# Restart Kodi service
echo "🔄 Restarting Kodi..."
ssh root@$COREELEC_IP "systemctl restart kodi"

echo "✅ Deployment complete!"
echo "📊 Monitor logs:"
echo "ssh root@$COREELEC_IP 'tail -f /storage/.kodi/temp/kodi.log | grep JELLYSKIP'"
