#!/usr/bin/env pwsh
# Autobahn Governance Detection Hook
# Routes infrastructure governance decisions to @seebohm

param()

# Read JSON from stdin
$input_json = [Console]::In.ReadToEnd() | ConvertFrom-Json

# Extract user message
$user_message = $input_json.userMessage -or $input_json.prompt -or ""

# Governance action keywords - must be present
$governance_keywords = @(
    "expand",
    "extend",
    "specify"
)

# Infrastructure file scope - must be mentioned
$file_scope_keywords = @(
    "roads/",
    "states/"
)

# Check for governance keyword
$has_governance = $false
foreach ($keyword in $governance_keywords) {
    if ($user_message -imatch $keyword) {
        $has_governance = $true
        break
    }
}

# Check for file scope
$has_scope = $false
foreach ($keyword in $file_scope_keywords) {
    if ($user_message -imatch [regex]::Escape($keyword)) {
        $has_scope = $true
        break
    }
}

# Build output
$output = @{
    hookSpecificOutput = @{
        hookEventName = "UserPromptSubmit"
        decision = if ($has_governance -and $has_scope) { "block" } else { "continue" }
    }
}

if ($has_governance -and $has_scope) {
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
