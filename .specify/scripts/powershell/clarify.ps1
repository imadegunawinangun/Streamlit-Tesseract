#!/usr/bin/env pwsh

# Clarification workflow for Spec-Driven Development
#
# This script implements the clarification workflow to identify and resolve ambiguities
# in feature specifications before proceeding to planning.
#
# Usage: ./clarify.ps1 [OPTIONS]

[CmdletBinding()]
param(
    [string]$Feature,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output @"
Usage: clarify.ps1 [OPTIONS]

Clarification workflow for Spec-Driven Development.

OPTIONS:
  -Feature <feature>    Specify feature branch to work on (defaults to current branch)
  -Help, -h           Show this help message

EXAMPLES:
  # Run clarification on current feature branch
  .\clarify.ps1
  
  # Run clarification on specific feature
  .\clarify.ps1 -Feature "001-new-feature"

"@
    exit 0
}

# Source common functions
. "$PSScriptRoot/common.ps1"

# Override feature branch if specified
if ($Feature) {
    $env:SPECIFY_FEATURE = $Feature
}

# Get feature paths and validate branch
$paths = Get-FeaturePathsEnv

if (-not (Test-FeatureBranch -Branch $paths.CURRENT_BRANCH -HasGit:$paths.HAS_GIT)) { 
    exit 1 
}

# Validate required directories and files
if (-not (Test-Path $paths.FEATURE_DIR -PathType Container)) {
    Write-Output "ERROR: Feature directory not found: $($paths.FEATURE_DIR)"
    Write-Output "Run /speckit.specify first to create the feature structure."
    exit 1
}

if (-not (Test-Path $paths.FEATURE_SPEC -PathType Leaf)) {
    Write-Output "ERROR: spec.md not found in $($paths.FEATURE_DIR)"
    Write-Output "Run /speckit.specify first to create the feature specification."
    exit 1
}

# Load the spec file
$specContent = Get-Content -Path $paths.FEATURE_SPEC -Raw

# Function to analyze ambiguity in the spec
function Test-SpecAmbiguity {
    param([string]$Content)
    
    $ambiguityMap = @{
        "Functional Scope & Behavior" = @{
            Status = "Clear"
            Issues = @()
        }
        "Domain & Data Model" = @{
            Status = "Clear"
            Issues = @()
        }
        "Interaction & UX Flow" = @{
            Status = "Clear"
            Issues = @()
        }
        "Non-Functional Quality Attributes" = @{
            Status = "Clear"
            Issues = @()
        }
        "Integration & External Dependencies" = @{
            Status = "Clear"
            Issues = @()
        }
        "Edge Cases & Failure Handling" = @{
            Status = "Clear"
            Issues = @()
        }
        "Constraints & Tradeoffs" = @{
            Status = "Clear"
            Issues = @()
        }
        "Terminology & Consistency" = @{
            Status = "Clear"
            Issues = @()
        }
        "Completion Signals" = @{
            Status = "Clear"
            Issues = @()
        }
        "Misc / Placeholders" = @{
            Status = "Clear"
            Issues = @()
        }
    }
    
    # Check for placeholders and TODO markers
    if ($Content -match 'TODO|FIXME|XXX|HACK|ACTION REQUIRED') {
        $ambiguityMap["Misc / Placeholders"].Status = "Missing"
        $ambiguityMap["Misc / Placeholders"].Issues += "Found TODO/FIXME markers in spec"
    }
    
    # Check for vague adjectives
    if ($Content -match 'robust|intuitive|seamless|flexible|powerful|efficient') {
        $ambiguityMap["Functional Scope & Behavior"].Status = "Partial"
        $ambiguityMap["Functional Scope & Behavior"].Issues += "Found vague adjectives that need quantification"
    }
    
    # Check for missing success criteria
    if ($Content -notmatch 'Success Criteria|Measurable Outcomes|SC-\d+') {
        $ambiguityMap["Completion Signals"].Status = "Missing"
        $ambiguityMap["Completion Signals"].Issues += "Missing measurable success criteria"
    }
    
    # Check for missing edge cases
    if ($Content -match 'Edge Cases' -and $Content -match '\[boundary condition\]|\[error scenario\]') {
        $ambiguityMap["Edge Cases & Failure Handling"].Status = "Partial"
        $ambiguityMap["Edge Cases & Failure Handling"].Issues += "Edge cases section contains placeholders"
    }
    
    # Check for missing non-functional requirements
    if ($Content -notmatch 'performance|latency|throughput|scalability|security|reliability') {
        $ambiguityMap["Non-Functional Quality Attributes"].Status = "Partial"
        $ambiguityMap["Non-Functional Quality Attributes"].Issues += "Missing explicit non-functional requirements"
    }
    
    return $ambiguityMap
}

# Function to generate clarification questions
function New-ClarificationQuestions {
    param([hashtable]$AmbiguityMap)
    
    $questions = @()
    
    # Generate questions based on ambiguity analysis
    if ($AmbiguityMap["Misc / Placeholders"].Status -eq "Missing") {
        $questions += @{
            Category = "Misc / Placeholders"
            Question = "What specific actions are needed for the ACTION REQUIRED items in the spec?"
            Type = "MultipleChoice"
            Options = @(
                @{Letter = "A"; Description = "Remove placeholder sections that dont apply"},
                @{Letter = "B"; Description = "Fill in all placeholder content with specific requirements"},
                @{Letter = "C"; Description = "Mark placeholders as deferred to implementation phase"}
            )
            Recommended = "B"
            Reason = "Completing placeholders now reduces downstream rework risk"
        }
    }
    
    if ($AmbiguityMap["Functional Scope & Behavior"].Status -eq "Partial") {
        $questions += @{
            Category = "Functional Scope & Behavior"
            Question = "How should we quantify the vague performance/quality terms in the spec?"
            Type = "MultipleChoice"
            Options = @(
                @{Letter = "A"; Description = "Define specific metrics (e.g., response time < 2s)"},
                @{Letter = "B"; Description = "Replace with concrete functional requirements"},
                @{Letter = "C"; Description = "Add measurable acceptance criteria"}
            )
            Recommended = "A"
            Reason = "Specific metrics enable objective testing and validation"
        }
    }
    
    if ($AmbiguityMap["Completion Signals"].Status -eq "Missing") {
        $questions += @{
            Category = "Completion Signals"
            Question = "What measurable success criteria should define when this feature is complete?"
            Type = "MultipleChoice"
            Options = @(
                @{Letter = "A"; Description = "User performance metrics (time to complete tasks)"},
                @{Letter = "B"; Description = "System performance metrics (throughput, latency)"},
                @{Letter = "C"; Description = "Business impact metrics (conversion, retention)"}
            )
            Recommended = "A"
            Reason = "User-focused metrics directly reflect feature value"
        }
    }
    
    if ($AmbiguityMap["Edge Cases & Failure Handling"].Status -eq "Partial") {
        $questions += @{
            Category = "Edge Cases & Failure Handling"
            Question = "What are the most critical edge cases to define for this feature?"
            Type = "MultipleChoice"
            Options = @(
                @{Letter = "A"; Description = "Input validation and boundary conditions"},
                @{Letter = "B"; Description = "Error recovery and user feedback"},
                @{Letter = "C"; Description = "Performance under load constraints"}
            )
            Recommended = "B"
            Reason = "Error handling directly impacts user experience"
        }
    }
    
    if ($AmbiguityMap["Non-Functional Quality Attributes"].Status -eq "Partial") {
        $questions += @{
            Category = "Non-Functional Quality Attributes"
            Question = "What are the key non-functional requirements for this feature?"
            Type = "ShortAnswer"
            Suggested = "Performance, security, accessibility"
            Reason = "These three cover most critical quality aspects"
        }
    }
    
    # Return top 5 questions by impact
    return $questions | Select-Object -First 5
}

# Function to ask a single question
function Ask-Question {
    param([hashtable]$Question)
    
    Write-Output "`n--- Question: $($Question.Category) ---"
    Write-Output $Question.Question
    
    if ($Question.Type -eq "MultipleChoice") {
        Write-Output "**Recommended:** Option $($Question.Recommended) - $($Question.Reason)"
        Write-Output ""
        Write-Output "Option - Description"
        Write-Output "-------- - -------------"
        
        foreach ($option in $Question.Options) {
            Write-Output "$($option.Letter) - $($option.Description)"
        }
        
        Write-Output "Short - Provide a different short answer (<=5 words)"
        Write-Output ""
        Write-Output "You can reply with the option letter (e.g., 'A'), accept the recommendation by saying 'yes' or 'recommended', or provide your own short answer."
        
        do {
            $response = Read-Host "Your answer"
            
            if ($response -match '^(yes|recommended)$') {
                return $Question.Recommended
            }
            
            if ($response -match '^[ABCDE]$') {
                return $response
            }
            
            if ($response.Length -le 5 -and $response.Trim() -ne "") {
                return $response.Trim()
            }
            
            Write-Output "Please provide a valid option letter or a short answer (<=5 words)."
        } while ($true)
    }
    else {
        Write-Output "**Suggested:** $($Question.Suggested) - $($Question.Reason)"
        Write-Output ""
        Write-Output "Format: Short answer (<=5 words). You can accept the suggestion by saying 'yes' or 'suggested', or provide your own answer."
        
        do {
            $response = Read-Host "Your answer"
            
            if ($response -match '^(yes|suggested)$') {
                return $Question.Suggested
            }
            
            if ($response.Length -le 5 -and $response.Trim() -ne "") {
                return $response.Trim()
            }
            
            Write-Output "Please provide a short answer (<=5 words)."
        } while ($true)
    }
}

# Function to update spec with clarification
function Update-SpecWithClarification {
    param(
        [string]$SpecPath,
        [string]$Question,
        [string]$Answer,
        [string]$Category
    )
    
    $content = Get-Content -Path $SpecPath -Raw
    $date = Get-Date -Format "yyyy-MM-dd"
    
    # Ensure Clarifications section exists
    if ($content -notmatch '## Clarifications') {
        # Find the position after the first major section (User Scenarios & Testing)
        $insertPos = $content.IndexOf("## User Scenarios & Testing")
        if ($insertPos -eq -1) {
            $insertPos = $content.IndexOf("##")
        }
        
        if ($insertPos -ne -1) {
            $clarificationsSection = "`n## Clarifications`n`n### Session $date`n`n"
            $content = $content.Insert($insertPos, $clarificationsSection)
        } else {
            $content += "`n## Clarifications`n`n### Session $date`n`n"
        }
    }
    
    # Ensure today's session section exists
    if ($content -notmatch "### Session $date") {
        $content += "`n### Session $date`n`n"
    }
    
    # Add the Q&A to the session
    $qaEntry = "- Q: $Question → A: $Answer`n"
    $sessionPos = $content.IndexOf("### Session $date")
    $nextSectionPos = $content.IndexOf("##", $sessionPos + 1)
    
    if ($nextSectionPos -eq -1) {
        $content += $qaEntry
    } else {
        $content = $content.Insert($nextSectionPos, $qaEntry)
    }
    
    # Apply the clarification to the appropriate section
    switch ($Category) {
        "Functional Scope & Behavior" {
            # Update Functional Requirements section
            if ($content -match "### Functional Requirements") {
                $frPos = $content.IndexOf("### Functional Requirements")
                $nextSectionPos = $content.IndexOf("##", $frPos + 1)
                
                $clarificationText = "`n- **Clarification**: $Question → $Answer`n"
                
                if ($nextSectionPos -eq -1) {
                    $content = $content.Insert($frPos, $clarificationText)
                } else {
                    $content = $content.Insert($nextSectionPos, $clarificationText)
                }
            }
        }
        "Completion Signals" {
            # Update Success Criteria section
            if ($content -match "### Measurable Outcomes") {
                $moPos = $content.IndexOf("### Measurable Outcomes")
                $nextSectionPos = $content.IndexOf("##", $moPos + 1)
                
                $clarificationText = "`n- **SC-Clarification**: $Question → $Answer`n"
                
                if ($nextSectionPos -eq -1) {
                    $content = $content.Insert($moPos, $clarificationText)
                } else {
                    $content = $content.Insert($nextSectionPos, $clarificationText)
                }
            }
        }
        "Edge Cases & Failure Handling" {
            # Update Edge Cases section
            if ($content -match "### Edge Cases") {
                $ecPos = $content.IndexOf("### Edge Cases")
                $nextSectionPos = $content.IndexOf("##", $ecPos + 1)
                
                $clarificationText = "`n- **Clarification**: $Question → $Answer`n"
                
                if ($nextSectionPos -eq -1) {
                    $content = $content.Insert($ecPos, $clarificationText)
                } else {
                    $content = $content.Insert($nextSectionPos, $clarificationText)
                }
            }
        }
    }
    
    # Save the updated spec
    Set-Content -Path $SpecPath -Value $content -NoNewline
}

# Main execution
Write-Output "Analyzing feature specification for ambiguities..."
$ambiguityMap = Test-SpecAmbiguity -Content $specContent

# Check if we have any meaningful ambiguities
$hasMeaningfulAmbiguities = $false
foreach ($category in $ambiguityMap.Keys) {
    if ($ambiguityMap[$category].Status -eq "Missing" -or $ambiguityMap[$category].Status -eq "Partial") {
        $hasMeaningfulAmbiguities = $true
        break
    }
}

if (-not $hasMeaningfulAmbiguities) {
    Write-Output "No critical ambiguities detected worth formal clarification."
    Write-Output "Proceeding to /speckit.plan is recommended."
    exit 0
}

# Generate clarification questions
$questions = New-ClarificationQuestions -AmbiguityMap $ambiguityMap

if ($questions.Count -eq 0) {
    Write-Output "No critical ambiguities detected worth formal clarification."
    Write-Output "Proceeding to /speckit.plan is recommended."
    exit 0
}

Write-Output "Found $($questions.Count) areas requiring clarification. Starting interactive session..."

# Interactive questioning loop
$questionsAsked = 0
$questionsAccepted = 0
$sectionsTouched = @()

foreach ($question in $questions) {
    if ($questionsAsked -ge 5) {
        break
    }
    
    $answer = Ask-Question -Question $question
    $questionsAsked++
    
    # Update spec with clarification
    Update-SpecWithClarification -SpecPath $paths.FEATURE_SPEC -Question $question.Question -Answer $answer -Category $question.Category
    
    $questionsAccepted++
    $sectionsTouched += $question.Category
    
    Write-Output "Clarification recorded and spec updated."
    
    # Check if user wants to continue
    if ($questionsAsked -lt $questions.Count) {
        $continue = Read-Host "Continue with next question? (y/n)"
        if ($continue -notmatch '^[Yy]') {
            break
        }
    }
}

# Generate coverage summary
Write-Output "`n=== Clarification Session Complete ==="
Write-Output "Questions asked: $questionsAsked"
Write-Output "Questions answered: $questionsAccepted"
Write-Output "Spec updated: $($paths.FEATURE_SPEC)"
Write-Output "Sections touched: $($sectionsTouched -join ', ')"

Write-Output "`n=== Coverage Summary ==="
Write-Output "Category - Status"
Write-Output "--------- - --------"

foreach ($category in $ambiguityMap.Keys) {
    $status = $ambiguityMap[$category].Status
    if ($sectionsTouched -contains $category) {
        $status = "Resolved"
    }
    Write-Output "$category - $status"
}

Write-Output "`nNext steps:"
if ($questionsAccepted -gt 0) {
    Write-Output "Review the updated spec for any remaining ambiguities"
    Write-Output "Run speckit.plan to create the implementation plan"
} else {
    Write-Output "Run speckit.plan to create the implementation plan"
}
