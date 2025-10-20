#!/bin/bash

# Common shell functions for Spec-Driven Development workflow
#
# This file provides common functions used across various workflow scripts.

# Function to get repository root
get_repo_root() {
    try_git_root=$(git rev-parse --show-toplevel 2>/dev/null || true)
    if [ $? -eq 0 ] && [ -n "$try_git_root" ]; then
        echo "$try_git_root"
        return
    fi
    
    # Fall back to script location for non-git repos
    echo "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
}

# Function to get current branch
get_current_branch() {
    # First check if SPECIFY_FEATURE environment variable is set
    if [ -n "$SPECIFY_FEATURE" ]; then
        echo "$SPECIFY_FEATURE"
        return
    fi
    
    # Then check git if available
    try_git_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)
    if [ $? -eq 0 ] && [ -n "$try_git_branch" ]; then
        echo "$try_git_branch"
        return
    fi
    
    # For non-git repos, try to find the latest feature directory
    local repo_root=$(get_repo_root)
    local specs_dir="$repo_root/specs"
    
    if [ -d "$specs_dir" ]; then
        local latest_feature=""
        local highest=0
        
        for dir in "$specs_dir"/*; do
            if [ -d "$dir" ]; then
                local basename_dir=$(basename "$dir")
                if [[ "$basename_dir" =~ ^([0-9]{3})- ]]; then
                    local num=${BASH_REMATCH[1]}
                    if [ "$num" -gt "$highest" ]; then
                        highest=$num
                        latest_feature="$basename_dir"
                    fi
                fi
            fi
        done
        
        if [ -n "$latest_feature" ]; then
            echo "$latest_feature"
            return
        fi
    fi
    
    # Final fallback
    echo "main"
}

# Function to test if git is available
test_has_git() {
    git rev-parse --show-toplevel >/dev/null 2>&1
    return $?
}

# Function to test if we're on a feature branch
test_feature_branch() {
    local branch="$1"
    local has_git="$2"
    
    # For non-git repos, we can't enforce branch naming but still provide output
    if [ "$has_git" = false ]; then
        echo "[specify] Warning: Git repository not detected; skipped branch validation" >&2
        return 0
    fi
    
    if [[ ! "$branch" =~ ^[0-9]{3}- ]]; then
        echo "ERROR: Not on a feature branch. Current branch: $branch" >&2
        echo "Feature branches should be named like: 001-feature-name" >&2
        return 1
    fi
    return 0
}

# Function to get feature directory
get_feature_dir() {
    local repo_root="$1"
    local branch="$2"
    echo "$repo_root/specs/$branch"
}

# Function to get all feature paths as JSON
get_feature_paths_env() {
    local repo_root=$(get_repo_root)
    local current_branch=$(get_current_branch)
    local has_git=false
    test_has_git && has_git=true
    local feature_dir=$(get_feature_dir "$repo_root" "$current_branch")
    
    cat << EOF
{
    "REPO_ROOT": "$repo_root",
    "CURRENT_BRANCH": "$current_branch",
    "HAS_GIT": $has_git,
    "FEATURE_DIR": "$feature_dir",
    "FEATURE_SPEC": "$feature_dir/spec.md",
    "IMPL_PLAN": "$feature_dir/plan.md",
    "TASKS": "$feature_dir/tasks.md",
    "RESEARCH": "$feature_dir/research.md",
    "DATA_MODEL": "$feature_dir/data-model.md",
    "QUICKSTART": "$feature_dir/quickstart.md",
    "CONTRACTS_DIR": "$feature_dir/contracts"
}
EOF
}

# Function to test if a file exists
test_file_exists() {
    local path="$1"
    local description="$2"
    
    if [ -f "$path" ]; then
        echo "  ✓ $description"
        return 0
    else
        echo "  ✗ $description"
        return 1
    fi
}

# Function to test if a directory has files
test_dir_has_files() {
    local path="$1"
    local description="$2"
    
    if [ -d "$path" ] && [ -n "$(ls -A "$path" 2>/dev/null)" ]; then
        echo "  ✓ $description"
        return 0
    else
        echo "  ✗ $description"
        return 1
    fi
}