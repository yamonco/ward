#!/bin/bash

# Default values
NUMBER=1
SHORT_NAME=""
FEATURE_DESC=""
USE_JSON=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --number)
            NUMBER="$2"
            shift 2
            ;;
        --short-name)
            SHORT_NAME="$2"
            shift 2
            ;;
        --json)
            USE_JSON=true
            shift
            ;;
        *)
            FEATURE_DESC="$1"
            shift
            ;;
    esac
done

# Generate branch name
BRANCH_NAME="${NUMBER}-${SHORT_NAME}"

# Create feature directory
FEATURE_DIR="specs/${BRANCH_NAME}"
mkdir -p "$FEATURE_DIR"

# Create spec file path
SPEC_FILE="$FEATURE_DIR/spec.md"

# Create basic spec structure
cat > "$SPEC_FILE" << EOF
# ${NUMBER}-${SHORT_NAME}

## Description
${FEATURE_DESC}

## User Scenarios & Testing
[To be defined]

## Functional Requirements
[To be defined]

## Success Criteria
[To be defined]

## Key Entities
[To be defined]

## Assumptions
[To be defined]
EOF

# Create and checkout branch
git checkout -b "$BRANCH_NAME"

# Output JSON if requested
if [ "$USE_JSON" = true ]; then
    cat << EOF
{
    "BRANCH_NAME": "$BRANCH_NAME",
    "SPEC_FILE": "$SPEC_FILE",
    "NUMBER": $NUMBER,
    "SHORT_NAME": "$SHORT_NAME"
}
EOF
fi

echo "Created feature: $BRANCH_NAME"
echo "Spec file: $SPEC_FILE"
echo "Branch checked out: $BRANCH_NAME"