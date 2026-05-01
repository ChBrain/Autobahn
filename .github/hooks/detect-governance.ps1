#!/usr/bin/env pwsh
# Autobahn Governance Detection Hook
# Routes infrastructure governance decisions to @seebohm

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

This appears to be an Autobahn network expansion decision. Please use the Seebohm governance agent:

\`\`\`
@seebohm
\`\`\`

Seebohm governs infrastructure through technical authority, precision specifications, and 30-year infrastructure strategy. Use him to specify network expansions, road connections, and infrastructure policies.
"@
}

$output | ConvertTo-Json -Depth 10 | Write-Output
exit 0
