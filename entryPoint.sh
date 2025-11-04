#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if containers are running
check_status() {
    if docker ps --filter "name=qdrant_" --format "{{.Names}}" | grep -q qdrant; then
        return 0  # Running
    else
        return 1  # Not running
    fi
}

# Function to display status
show_status() {
    echo -e "\n${BLUE}=== Container Status ===${NC}"
    if check_status; then
        echo -e "${GREEN}✓ Containers are RUNNING${NC}"
        docker ps --filter "name=qdrant_" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        echo -e "${RED}✗ Containers are STOPPED${NC}"
    fi
    echo ""
}

# Function to start containers
start_containers() {
    if check_status; then
        echo -e "${YELLOW}Containers are already running!${NC}"
    else
        echo -e "${GREEN}Starting containers...${NC}"
        docker compose up -d
        echo -e "${GREEN}✓ Containers started successfully!${NC}"
        show_status
    fi
}

# Function to stop containers
stop_containers() {
    if check_status; then
        echo -e "${YELLOW}Stopping containers...${NC}"
        docker compose down
        echo -e "${GREEN}✓ Containers stopped successfully!${NC}"
    else
        echo -e "${YELLOW}Containers are already stopped!${NC}"
    fi
}

# Function to restart containers
restart_containers() {
    echo -e "${YELLOW}Restarting containers...${NC}"
    docker compose restart
    echo -e "${GREEN}✓ Containers restarted successfully!${NC}"
    show_status
}

# Function to rebuild containers
rebuild_containers() {
    echo -e "${YELLOW}Rebuilding containers...${NC}"
    docker compose down
    docker compose build --no-cache
    docker compose up -d
    echo -e "${GREEN}✓ Containers rebuilt successfully!${NC}"
    show_status
}

# Function to view logs
view_logs() {
    echo -e "${BLUE}Select service to view logs:${NC}"
    echo "1. API (qdrant_api)"
    echo "2. Qdrant DB (qdrant_vector_db)"
    echo "3. Web UI (qdrant_web_ui)"
    echo "4. All services"
    read -p "Enter choice [1-4]: " log_choice
    
    case $log_choice in
        1) docker logs -f qdrant_api ;;
        2) docker logs -f qdrant_vector_db ;;
        3) docker logs -f qdrant_web_ui ;;
        4) docker compose logs -f ;;
        *) echo -e "${RED}Invalid choice${NC}" ;;
    esac
}

# Function to open URLs
open_services() {
    echo -e "\n${BLUE}=== Service URLs ===${NC}"
    echo "API: http://localhost:8000"
    echo "API Docs (Swagger): http://localhost:8000/docs"
    echo "API Docs (ReDoc): http://localhost:8000/redoc"
    echo "Qdrant Dashboard: http://localhost:6333/dashboard"
    echo "Web UI: http://localhost:3000"
    echo ""
    read -p "Open services in browser? (y/n): " open_choice
    if [[ $open_choice == "y" || $open_choice == "Y" ]]; then
        open http://localhost:3000
        open http://localhost:8000/docs
    fi
}

# Main menu
main_menu() {
    while true; do
        show_status
        echo -e "${BLUE}=== Qdrant Vector DB Management ===${NC}"
        
        if check_status; then
            echo -e "1. ${RED}Stop containers${NC}"
            echo "2. Restart containers"
            echo "3. View logs"
            echo "4. Rebuild containers"
            echo "5. Open service URLs"
            echo "6. Check health"
            echo "0. Exit"
        else
            echo -e "1. ${GREEN}Start containers${NC}"
            echo "2. Rebuild and start"
            echo "3. View logs (if available)"
            echo "0. Exit"
        fi
        
        echo ""
        read -p "Enter your choice: " choice
        
        case $choice in
            1)
                if check_status; then
                    stop_containers
                else
                    start_containers
                fi
                ;;
            2)
                if check_status; then
                    restart_containers
                else
                    rebuild_containers
                fi
                ;;
            3)
                view_logs
                ;;
            4)
                if check_status; then
                    rebuild_containers
                fi
                ;;
            5)
                if check_status; then
                    open_services
                fi
                ;;
            6)
                if check_status; then
                    echo -e "\n${BLUE}Checking API health...${NC}"
                    curl -s http://localhost:8000/health | jq '.' || echo -e "${RED}Health check failed${NC}"
                fi
                ;;
            0)
                echo -e "${GREEN}Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid choice. Please try again.${NC}"
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
        clear
    done
}

# Entry point
clear
echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Qdrant Vector DB Manager           ║${NC}"
echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo ""

main_menu