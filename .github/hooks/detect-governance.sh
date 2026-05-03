#!/bin/bash
# Autobahn Governance Detection Hook (Linux/macOS)
# Routes infrastructure governance decisions to @minister-transport

# Read JSON from stdin
input_json=$(cat)

# Extract user message
user_message=$(echo "$input_json" | grep -o '"userMessage":"[^"]*' | cut -d'"' -f4)
if [ -z "$user_message" ]; then
  user_message=$(echo "$input_json" | grep -o '"prompt":"[^"]*' | cut -d'"' -f4)
fi

# Governance decision keywords
is_governance=false
for keyword in "expand" "extend" "specify" "network.*expansion" "infrastructure.*decision" "bundesland" "road.*specification" "network.*specification"; do
  if echo "$user_message" | grep -qi "$keyword"; then
    is_governance=true
    break
  fi
done

# Build output
if [ "$is_governance" = true ]; then
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "decision": "block"
  },
  "systemMessage": "🏛️ **Infrastructure Governance**\n\nThis appears to be an Autobahn network expansion or infrastructure governance decision. Please use the transport minister governance agent:\n\n\`\`\`\n@minister-transport\n\`\`\`\n\nThe minister-transport agent governs infrastructure through technical authority, precision specifications, and strategic vision. It dynamically selects the appropriate historical or current minister based on your context. Use it to specify network expansions, road connections, regulatory changes, and infrastructure policies."
}
EOF
else
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "decision": "continue"
  }
}
EOF
fi

exit 0
