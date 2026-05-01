#!/usr/bin/env pwsh
# Autobahn Release Detection Hook
# Checks for release keywords and routes to autobahn-release agent

param()

# Read JSON from stdin
$input_json = [Console]::In.ReadToEnd() | ConvertFrom-Json

# Extract user message
$user_message = $input_json.userMessage -or $input_json.prompt -or ""

# Release-related keywords
$release_keywords = @(
    "release",
    "bump version", 
    "bump_version",
    "v0\.", 
    "v1\.",
    "v2\.",
    "create tag",
    "git tag",
    "deploy",
    "0\.\d+\.\d+",  # semantic versioning
)

# Check if message contains release keywords
$contains_release = $false
foreach ($keyword in $release_keywords) {
    if ($user_message -match $keyword) {
        $contains_release = $true
        break
    }
}

# Build output
$output = @{
    hookSpecificOutput = @{
        hookEventName = "UserPromptSubmit"
        decision = if ($contains_release) { "block" } else { "continue" }
    }
}

if ($contains_release) {
    $output.systemMessage = @"
🔒 **Release Detected**

This appears to be a release request. Please use the dedicated Autobahn release agent:

\`\`\`
/autobahn-release
@autobahn-release please release X.Y.Z
\`\`\`

The release agent enforces safety gates and requires explicit approval before:
- Merging PRs to main
- Creating release tags
- Creating GitHub Releases

This prevents accidental bypasses and keeps your releases safe.
"@
}

$output | ConvertTo-Json -Depth 10 | Write-Output
exit 0
