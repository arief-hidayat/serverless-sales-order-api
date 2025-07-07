#!/bin/bash

# Cleanup script for removing unused directories and files

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting cleanup process...${NC}"

# Check if events directory exists
if [ -d "../events" ]; then
    # Check if the directory is empty
    if [ -z "$(ls -A ../events)" ]; then
        echo -e "${YELLOW}Removing empty events directory...${NC}"
        rmdir ../events
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Successfully removed empty events directory.${NC}"
        else
            echo -e "${YELLOW}Failed to remove events directory. Please check permissions.${NC}"
        fi
    else
        echo -e "${YELLOW}Events directory is not empty. Please check its contents before removal.${NC}"
        ls -la ../events
    fi
else
    echo -e "${GREEN}Events directory does not exist. No cleanup needed.${NC}"
fi

echo -e "${GREEN}Cleanup process completed.${NC}"