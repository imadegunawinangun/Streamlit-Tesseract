#!/bin/bash

# Clarification workflow for Spec-Driven Development
#
# This script implements the clarification workflow to identify and resolve ambiguities
# in feature specifications before proceeding to planning.
#
# Usage: ./clarify.sh [OPTIONS]

set -e

# Default values
FEATURE=""
HELP=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -Feature|--Feature)
            FEATURE="$2"
            shift 2
            ;;
        -Help|--Help|-h)
            HELP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            HELP=true
            shift
            ;;
    esac
done

# Show help if requested
if [ "$HELP" = true ]; then
    cat << EOF
Usage: clarify.sh [OPTIONS]

Clarification workflow for Spec-Driven Development.

OPTIONS:
  -Feature <feature>    Specify feature branch to work on (defaults to current branch)
  -Help, -h           Show this help message

EXAMPLES:
  # Run clarification on current feature branch
  ./clarify.sh
  
  # Run clarification on specific feature
  ./clarify.sh -Feature "001-new-feature"

EOF
    exit 0
fi

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Override feature branch if specified
if [ -n "$FEATURE" ]; then
    export SPECIFY_FEATURE="$FEATURE"
fi

# Get feature paths and validate branch
paths=$(get_feature_paths_env)
REPO_ROOT=$(echo "$paths" | jq -r '.REPO_ROOT')
CURRENT_BRANCH=$(echo "$paths" | jq -r '.CURRENT_BRANCH')
HAS_GIT=$(echo "$paths" | jq -r '.HAS_GIT')
FEATURE_DIR=$(echo "$paths" | jq -r '.FEATURE_DIR')
FEATURE_SPEC=$(echo "$paths" | jq -r '.FEATURE_SPEC')

if ! test_feature_branch "$CURRENT_BRANCH" "$HAS_GIT"; then 
    exit 1 
fi

# Validate required directories and files
if [ ! -d "$FEATURE_DIR" ]; then
    echo "ERROR: Feature directory not found: $FEATURE_DIR"
    echo "Run /speckit.specify first to create the feature structure."
    exit 1
fi

if [ ! -f "$FEATURE_SPEC" ]; then
    echo "ERROR: spec.md not found in $FEATURE_DIR"
    echo "Run /speckit.specify first to create the feature specification."
    exit 1
fi

# Load the spec file
spec_content=$(cat "$FEATURE_SPEC")

# Function to analyze ambiguity in the spec
test_spec_ambiguity() {
    local content="$1"
    
    # Create a JSON object with ambiguity analysis
    cat << EOF
{
    "Functional Scope & Behavior": {
        "Status": "Clear",
        "Issues": []
    },
    "Domain & Data Model": {
        "Status": "Clear",
        "Issues": []
    },
    "Interaction & UX Flow": {
        "Status": "Clear",
        "Issues": []
    },
    "Non-Functional Quality Attributes": {
        "Status": "Clear",
        "Issues": []
    },
    "Integration & External Dependencies": {
        "Status": "Clear",
        "Issues": []
    },
    "Edge Cases & Failure Handling": {
        "Status": "Clear",
        "Issues": []
    },
    "Constraints & Tradeoffs": {
        "Status": "Clear",
        "Issues": []
    },
    "Terminology & Consistency": {
        "Status": "Clear",
        "Issues": []
    },
    "Completion Signals": {
        "Status": "Clear",
        "Issues": []
    },
    "Misc / Placeholders": {
        "Status": "Clear",
        "Issues": []
    }
}
EOF
}

# Function to check for placeholders and TODO markers
check_placeholders() {
    local content="$1"
    
    if echo "$content" | grep -q -E 'TODO|FIXME|XXX|HACK|ACTION REQUIRED'; then
        echo "true"
    else
        echo "false"
    fi
}

# Function to check for vague adjectives
check_vague_adjectives() {
    local content="$1"
    
    if echo "$content" | grep -q -E 'robust|intuitive|seamless|flexible|powerful|efficient'; then
        echo "true"
    else
        echo "false"
    fi
}

# Function to check for missing success criteria
check_success_criteria() {
    local content="$1"
    
    if echo "$content" | grep -q -E 'Success Criteria|Measurable Outcomes|SC-\d+'; then
        echo "false"
    else
        echo "true"
    fi
}

# Function to check for missing edge cases
check_edge_cases() {
    local content="$1"
    
    if echo "$content" | grep -q -E 'Edge Cases' && echo "$content" | grep -q -E '\[boundary condition\]|\[error scenario\]'; then
        echo "true"
    else
        echo "false"
    fi
}

# Function to check for missing non-functional requirements
check_non_functional() {
    local content="$1"
    
    if echo "$content" | grep -q -E 'performance|latency|throughput|scalability|security|reliability'; then
        echo "false"
    else
        echo "true"
    fi
}

# Function to generate clarification questions
generate_clarification_questions() {
    local content="$1"
    local has_placeholders="$2"
    local has_vague_adjectives="$3"
    local missing_success_criteria="$4"
    local missing_edge_cases="$5"
    local missing_non_functional="$6"
    
    local questions="[]"
    
    # Generate questions based on ambiguity analysis
    if [ "$has_placeholders" = "true" ]; then
        questions=$(echo "$questions" | jq '. += [{
            "Category": "Misc / Placeholders",
            "Question": "What specific actions are needed for the ACTION REQUIRED items in the spec?",
            "Type": "MultipleChoice",
            "Options": [
                {"Letter": "A", "Description": "Remove placeholder sections that dont apply"},
                {"Letter": "B", "Description": "Fill in all placeholder content with specific requirements"},
                {"Letter": "C", "Description": "Mark placeholders as deferred to implementation phase"}
            ],
            "Recommended": "B",
            "Reason": "Completing placeholders now reduces downstream rework risk"
        }]')
    fi
    
    if [ "$has_vague_adjectives" = "true" ]; then
        questions=$(echo "$questions" | jq '. += [{
            "Category": "Functional Scope & Behavior",
            "Question": "How should we quantify the vague performance/quality terms in the spec?",
            "Type": "MultipleChoice",
            "Options": [
                {"Letter": "A", "Description": "Define specific metrics (e.g., response time < 2s)"},
                {"Letter": "B", "Description": "Replace with concrete functional requirements"},
                {"Letter": "C", "Description": "Add measurable acceptance criteria"}
            ],
            "Recommended": "A",
            "Reason": "Specific metrics enable objective testing and validation"
        }]')
    fi
    
    if [ "$missing_success_criteria" = "true" ]; then
        questions=$(echo "$questions" | jq '. += [{
            "Category": "Completion Signals",
            "Question": "What measurable success criteria should define when this feature is complete?",
            "Type": "MultipleChoice",
            "Options": [
                {"Letter": "A", "Description": "User performance metrics (time to complete tasks)"},
                {"Letter": "B", "Description": "System performance metrics (throughput, latency)"},
                {"Letter": "C", "Description": "Business impact metrics (conversion, retention)"}
            ],
            "Recommended": "A",
            "Reason": "User-focused metrics directly reflect feature value"
        }]')
    fi
    
    if [ "$missing_edge_cases" = "true" ]; then
        questions=$(echo "$questions" | jq '. += [{
            "Category": "Edge Cases & Failure Handling",
            "Question": "What are the most critical edge cases to define for this feature?",
            "Type": "MultipleChoice",
            "Options": [
                {"Letter": "A", "Description": "Input validation and boundary conditions"},
                {"Letter": "B", "Description": "Error recovery and user feedback"},
                {"Letter": "C", "Description": "Performance under load constraints"}
            ],
            "Recommended": "B",
            "Reason": "Error handling directly impacts user experience"
        }]')
    fi
    
    if [ "$missing_non_functional" = "true" ]; then
        questions=$(echo "$questions" | jq '. += [{
            "Category": "Non-Functional Quality Attributes",
            "Question": "What are the key non-functional requirements for this feature?",
            "Type": "ShortAnswer",
            "Suggested": "Performance, security, accessibility",
            "Reason": "These three cover most critical quality aspects"
        }]')
    fi
    
    # Return top 5 questions
    echo "$questions" | jq '.[0:5]'
}

# Function to ask a single question
ask_question() {
    local question="$1"
    
    echo ""
    echo "--- Question: $(echo "$question" | jq -r '.Category') ---"
    echo "$(echo "$question" | jq -r '.Question')"
    
    local question_type=$(echo "$question" | jq -r '.Type')
    
    if [ "$question_type" = "MultipleChoice" ]; then
        local recommended=$(echo "$question" | jq -r '.Recommended')
        local reason=$(echo "$question" | jq -r '.Reason')
        
        echo "**Recommended:** Option $recommended - $reason"
        echo ""
        echo "| Option | Description |"
        echo "|--------|-------------|"
        
        echo "$question" | jq -r '.Options[] | "| \(.Letter) | \(.Description) |"'
        echo "| Short | Provide a different short answer (<=5 words) |"
        echo ""
        echo "You can reply with the option letter (e.g., 'A'), accept the recommendation by saying 'yes' or 'recommended', or provide your own short answer."
        
        while true; do
            read -p "Your answer: " response
            
            if [[ "$response" =~ ^(yes|recommended)$ ]]; then
                echo "$recommended"
                return
            fi
            
            if [[ "$response" =~ ^[ABCDE]$ ]]; then
                echo "$response"
                return
            fi
            
            if [ ${#response} -le 5 ] && [ -n "$(echo "$response" | tr -d ' ')" ]; then
                echo "$(echo "$response" | xargs)"
                return
            fi
            
            echo "Please provide a valid option letter or a short answer (<=5 words)."
        done
    else
        local suggested=$(echo "$question" | jq -r '.Suggested')
        local reason=$(echo "$question" | jq -r '.Reason')
        
        echo "**Suggested:** $suggested - $reason"
        echo ""
        echo "Format: Short answer (<=5 words). You can accept the suggestion by saying 'yes' or 'suggested', or provide your own answer."
        
        while true; do
            read -p "Your answer: " response
            
            if [[ "$response" =~ ^(yes|suggested)$ ]]; then
                echo "$suggested"
                return
            fi
            
            if [ ${#response} -le 5 ] && [ -n "$(echo "$response" | tr -d ' ')" ]; then
                echo "$(echo "$response" | xargs)"
                return
            fi
            
            echo "Please provide a short answer (<=5 words)."
        done
    fi
}

# Function to update spec with clarification
update_spec_with_clarification() {
    local spec_path="$1"
    local question="$2"
    local answer="$3"
    local category="$4"
    
    local content=$(cat "$spec_path")
    local date=$(date +%Y-%m-%d)
    
    # Ensure Clarifications section exists
    if ! echo "$content" | grep -q "## Clarifications"; then
        # Find the position after the first major section (User Scenarios & Testing)
        if echo "$content" | grep -q "## User Scenarios & Testing"; then
            content=$(echo "$content" | sed '/## User Scenarios & Testing/i\\n## Clarifications\n\n### Session '"$date"'\n\n')
        else
            content="$content"$'\n\n## Clarifications\n\n### Session '"$date"'\n\n'
        fi
    fi
    
    # Ensure today's session section exists
    if ! echo "$content" | grep -q "### Session $date"; then
        content="$content"$'\n\n### Session '"$date"'\n\n'
    fi
    
    # Add the Q&A to the session
    local qa_entry="- Q: $question → A: $answer"$'\n'
    
    # Insert before the next ## section or at the end
    if echo "$content" | grep -A1 "### Session $date" | grep -q "##"; then
        # Insert before the next ## section
        content=$(echo "$content" | sed "/### Session $date/,/^##/ {
            /^##/i\\$qa_entry
        }")
    else
        # Append to the end
        content="$content$qa_entry"
    fi
    
    # Apply the clarification to the appropriate section
    case "$category" in
        "Functional Scope & Behavior")
            # Update Functional Requirements section
            if echo "$content" | grep -q "### Functional Requirements"; then
                local clarification_text=$'\n'"- **Clarification**: $question → $answer"$'\n'
                content=$(echo "$content" | sed '/### Functional Requirements/,/^##/ {
                    /^##/i\\$clarification_text
                }')
            fi
            ;;
        "Completion Signals")
            # Update Success Criteria section
            if echo "$content" | grep -q "### Measurable Outcomes"; then
                local clarification_text=$'\n'"- **SC-Clarification**: $question → $answer"$'\n'
                content=$(echo "$content" | sed '/### Measurable Outcomes/,/^##/ {
                    /^##/i\\$clarification_text
                }')
            fi
            ;;
        "Edge Cases & Failure Handling")
            # Update Edge Cases section
            if echo "$content" | grep -q "### Edge Cases"; then
                local clarification_text=$'\n'"- **Clarification**: $question → $answer"$'\n'
                content=$(echo "$content" | sed '/### Edge Cases/,/^##/ {
                    /^##/i\\$clarification_text
                }')
            fi
            ;;
    esac
    
    # Save the updated spec
    echo "$content" > "$spec_path"
}

# Main execution
echo "Analyzing feature specification for ambiguities..."

# Check for various ambiguity indicators
has_placeholders=$(check_placeholders "$spec_content")
has_vague_adjectives=$(check_vague_adjectives "$spec_content")
missing_success_criteria=$(check_success_criteria "$spec_content")
missing_edge_cases=$(check_edge_cases "$spec_content")
missing_non_functional=$(check_non_functional "$spec_content")

# Check if we have any meaningful ambiguities
has_meaningful_ambiguities=false
if [ "$has_placeholders" = "true" ] || [ "$has_vague_adjectives" = "true" ] || [ "$missing_success_criteria" = "true" ] || [ "$missing_edge_cases" = "true" ] || [ "$missing_non_functional" = "true" ]; then
    has_meaningful_ambiguities=true
fi

if [ "$has_meaningful_ambiguities" = false ]; then
    echo "No critical ambiguities detected worth formal clarification."
    echo "Proceeding to /speckit.plan is recommended."
    exit 0
fi

# Generate clarification questions
questions_json=$(generate_clarification_questions "$spec_content" "$has_placeholders" "$has_vague_adjectives" "$missing_success_criteria" "$missing_edge_cases" "$missing_non_functional")
questions_count=$(echo "$questions_json" | jq '. | length')

if [ "$questions_count" -eq 0 ]; then
    echo "No critical ambiguities detected worth formal clarification."
    echo "Proceeding to /speckit.plan is recommended."
    exit 0
fi

echo "Found $questions_count areas requiring clarification. Starting interactive session..."

# Interactive questioning loop
questions_asked=0
questions_accepted=0
sections_touched=()

for ((i=0; i<questions_count; i++)); do
    if [ $questions_asked -ge 5 ]; then
        break
    fi
    
    question=$(echo "$questions_json" | jq -r ".[$i]")
    answer=$(ask_question "$question")
    questions_asked=$((questions_asked + 1))
    
    # Update spec with clarification
    question_text=$(echo "$question" | jq -r '.Question')
    category=$(echo "$question" | jq -r '.Category')
    
    update_spec_with_clarification "$FEATURE_SPEC" "$question_text" "$answer" "$category"
    
    questions_accepted=$((questions_accepted + 1))
    sections_touched+=("$category")
    
    echo "✓ Clarification recorded and spec updated."
    
    # Check if user wants to continue
    if [ $questions_asked -lt $questions_count ]; then
        read -p "Continue with next question? (y/n) " continue_answer
        if [[ ! "$continue_answer" =~ ^[Yy]$ ]]; then
            break
        fi
    fi
done

# Generate coverage summary
echo ""
echo "=== Clarification Session Complete ==="
echo "Questions asked: $questions_asked"
echo "Questions answered: $questions_accepted"
echo "Spec updated: $FEATURE_SPEC"
echo "Sections touched: $(IFS=', '; echo "${sections_touched[*]}")"

echo ""
echo "=== Coverage Summary ==="
echo "| Category | Status |"
echo "|----------|--------|"

# Create a simple status report
if [ "$has_placeholders" = "true" ]; then
    if [[ " ${sections_touched[*]} " =~ " Misc / Placeholders " ]]; then
        echo "| Misc / Placeholders | Resolved |"
    else
        echo "| Misc / Placeholders | Outstanding |"
    fi
else
    echo "| Misc / Placeholders | Clear |"
fi

if [ "$has_vague_adjectives" = "true" ]; then
    if [[ " ${sections_touched[*]} " =~ " Functional Scope & Behavior " ]]; then
        echo "| Functional Scope & Behavior | Resolved |"
    else
        echo "| Functional Scope & Behavior | Outstanding |"
    fi
else
    echo "| Functional Scope & Behavior | Clear |"
fi

if [ "$missing_success_criteria" = "true" ]; then
    if [[ " ${sections_touched[*]} " =~ " Completion Signals " ]]; then
        echo "| Completion Signals | Resolved |"
    else
        echo "| Completion Signals | Outstanding |"
    fi
else
    echo "| Completion Signals | Clear |"
fi

if [ "$missing_edge_cases" = "true" ]; then
    if [[ " ${sections_touched[*]} " =~ " Edge Cases & Failure Handling " ]]; then
        echo "| Edge Cases & Failure Handling | Resolved |"
    else
        echo "| Edge Cases & Failure Handling | Outstanding |"
    fi
else
    echo "| Edge Cases & Failure Handling | Clear |"
fi

if [ "$missing_non_functional" = "true" ]; then
    if [[ " ${sections_touched[*]} " =~ " Non-Functional Quality Attributes " ]]; then
        echo "| Non-Functional Quality Attributes | Resolved |"
    else
        echo "| Non-Functional Quality Attributes | Outstanding |"
    fi
else
    echo "| Non-Functional Quality Attributes | Clear |"
fi

echo ""
echo "Next steps:"
if [ $questions_accepted -gt 0 ]; then
    echo "✓ Review the updated spec for any remaining ambiguities"
    echo "✓ Run /speckit.plan to create the implementation plan"
else
    echo "✓ Run /speckit.plan to create the implementation plan"
fi