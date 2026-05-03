#!/usr/bin/env pwsh
# Autobahn Governance Detection Hook
# Routes infrastructure governance decisions to @minister-transport

param()

# Read JSON from stdin
$input_json = [Console]::In.ReadToEnd() | ConvertFrom-Json

# Extract user message
$user_message = $input_json.userMessage -or $input_json.prompt -or ""

# Governance decision keywords
$governance_keywords = @(
    "expand",
    "extend",
    "specify",
    "network.*expansion",
    "infrastructure.*decision",
    "bundesland",
    "road.*specification",
    "network.*specification"
)

# Check for governance keyword
$is_governance = $false
foreach ($keyword in $governance_keywords) {
    if ($user_message -imatch $keyword) {
        $is_governance = $true
        break
    }
}

# Build output
$output = @{
    hookSpecificOutput = @{
        hookEventName = "UserPromptSubmit"
        decision = if ($is_governance) { "block" } else { "continue" }
    }
}

if ($is_governance) {
    $output.systemMessage = @"
🏛️ **Infrastructure Governance**

This appears to be an Autobahn network expansion or infrastructure governance decision. Please use the transport minister governance agent:

\`\`\`
@minister-transport
\`\`\`

The minister-transport agent governs infrastructure through technical authority, precision specifications, and strategic vision. It dynamically selects the appropriate historical or current minister based on your context. Use it to specify network expansions, road connections, regulatory changes, and infrastructure policies.
"@
}

$output | ConvertTo-Json -Depth 10 | Write-Output
exit 0
