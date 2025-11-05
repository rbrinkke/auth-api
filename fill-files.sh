#!/bin/bash

# =============================================================================
# Auth API File Filler (INTERACTIEF)
# =============================================================================
# Dit script opent elk bestand 1-voor-1 in je editor
# Jij plakt de inhoud, sluit het bestand, en het gaat door naar het volgende
# =============================================================================

set -e

# Kleuren
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Auth API File Filler (INTERACTIEF)             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check of we in de juiste directory zijn
if [ ! -f "requirements.txt" ] || [ ! -d "app" ]; then
    echo -e "${RED}❌ Error: Voer dit script uit vanuit de auth-api directory!${NC}"
    echo ""
    echo "Eerst runnen:"
    echo "  ./create-structure.sh"
    echo "  cd [path-to-auth-api]"
    echo "  ./fill-files.sh"
    exit 1
fi

# Vraag welke editor te gebruiken
echo -e "${YELLOW}Welke editor wil je gebruiken?${NC}"
echo ""
echo "  1) nano (terminal editor, makkelijk)"
echo "  2) vim (terminal editor, advanced)"
echo "  3) code (VS Code)"
echo "  4) gedit (GUI editor)"
echo ""
read -p "Kies optie (1/2/3/4): " editor_choice

case $editor_choice in
    1) EDITOR="nano" ;;
    2) EDITOR="vim" ;;
    3) EDITOR="code --wait" ;;
    4) EDITOR="gedit" ;;
    *) EDITOR="nano" ;;
esac

echo ""
echo -e "${GREEN}✓${NC} Editor: $EDITOR"
echo ""

# Lijst van bestanden in volgorde van belangrijkheid
FILES=(
    # Start met configuratie
    "requirements.txt|Dependencies"
    ".env.example|Environment variables"
    ".gitignore|Git ignore"
    ".dockerignore|Docker ignore"
    
    # Core configuratie
    "app/config.py|Settings & configuration"
    
    # Core utilities
    "app/core/security.py|Password hashing (Argon2)"
    "app/core/tokens.py|JWT token logic"
    "app/core/redis_client.py|Redis token storage"
    
    # Database
    "app/db/connection.py|Database connection pool"
    "app/db/procedures.py|Stored procedure wrappers"
    
    # Schemas
    "app/schemas/user.py|User Pydantic models"
    "app/schemas/auth.py|Auth request/response models"
    
    # Services
    "app/services/email_service.py|Email service client"
    
    # Routes (belangrijkste endpoints)
    "app/routes/register.py|POST /auth/register"
    "app/routes/login.py|POST /auth/login"
    "app/routes/verify.py|GET /auth/verify"
    "app/routes/refresh.py|POST /auth/refresh (rotation!)"
    "app/routes/logout.py|POST /auth/logout"
    "app/routes/password_reset.py|Password reset endpoints"
    
    # Main app
    "app/main.py|FastAPI application"
    
    # Init files (laat leeg of simpele comment)
    "app/__init__.py|App package init"
    "app/core/__init__.py|Core package init"
    "app/db/__init__.py|DB package init"
    "app/schemas/__init__.py|Schemas package init"
    "app/services/__init__.py|Services package init"
    "app/routes/__init__.py|Routes package init"
    
    # Docker
    "Dockerfile|Docker image"
    "docker-compose.yml|Docker setup"
    
    # Database
    "stored_procedures.sql|PostgreSQL schema + SP's"
    
    # Scripts
    "quickstart.sh|Quick start script"
    
    # Documentation
    "README.md|Setup guide"
    "ARCHITECTURE.md|Architecture docs"
    "PROJECT_STRUCTURE.md|Project overview"
)

TOTAL=${#FILES[@]}
CURRENT=0

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Klaar om te starten!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "Hoe het werkt:"
echo "  1. Editor opent een bestand"
echo "  2. Plak de inhoud erin (van mijn output)"
echo "  3. Save & close"
echo "  4. Script gaat automatisch door naar volgende"
echo ""
echo "Tips:"
echo "  - Heb mijn output open in een ander venster"
echo "  - Copy/paste de hele file content"
echo "  - ${YELLOW}__init__.py files kun je leeg laten${NC}"
echo ""
read -p "Druk Enter om te beginnen..." start

echo ""

for item in "${FILES[@]}"; do
    CURRENT=$((CURRENT + 1))
    
    # Split op |
    FILE=$(echo $item | cut -d'|' -f1)
    DESC=$(echo $item | cut -d'|' -f2)
    
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}[$CURRENT/$TOTAL]${NC} $FILE"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "📝 ${YELLOW}$DESC${NC}"
    echo ""
    
    # Special behandeling voor __init__.py files
    if [[ $FILE == *"__init__.py" ]]; then
        echo -e "${YELLOW}Dit is een __init__.py file.${NC}"
        echo "Wil je:"
        echo "  1) Leeg laten (druk Enter)"
        echo "  2) Openen om content toe te voegen"
        read -p "Keuze (1/2): " init_choice
        
        if [ "$init_choice" == "1" ]; then
            echo "# Empty init file" > "$FILE"
            echo -e "${GREEN}✓${NC} Leeg init file aangemaakt"
            continue
        fi
    fi
    
    # Check of file bestaat
    if [ ! -f "$FILE" ]; then
        echo -e "${RED}⚠ File bestaat niet: $FILE${NC}"
        read -p "Overslaan? (y/n): " skip
        if [ "$skip" == "y" ]; then
            continue
        fi
    fi
    
    # Toon instructie
    echo -e "${YELLOW}Instructie:${NC}"
    echo "  1. Editor opent zo meteen"
    echo "  2. Plak de inhoud voor '$FILE' erin"
    echo "  3. Save en sluit"
    echo ""
    read -p "Druk Enter om editor te openen..." cont
    
    # Open editor
    $EDITOR "$FILE"
    
    # Check of er iets in staat
    if [ -s "$FILE" ]; then
        LINES=$(wc -l < "$FILE")
        echo -e "${GREEN}✓${NC} File opgeslagen ($LINES regels)"
    else
        echo -e "${YELLOW}⚠${NC} File is leeg - is dit correct?"
        read -p "Doorgaan? (y/n): " proceed
        if [ "$proceed" != "y" ]; then
            echo "Opnieuw openen..."
            $EDITOR "$FILE"
        fi
    fi
    
    # Kleine pauze
    sleep 0.5
done

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ KLAAR! Alle bestanden zijn gevuld!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "Volgende stappen:"
echo ""
echo "  1. Test de setup:"
echo -e "     ${BLUE}./quickstart.sh${NC}"
echo ""
echo "  2. Of handmatig:"
echo -e "     ${BLUE}docker-compose up -d${NC}"
echo ""
echo "  3. Maak database schema:"
echo -e "     ${BLUE}docker exec -i auth-postgres psql -U activity_user -d activity_db < stored_procedures.sql${NC}"
echo ""
echo "  4. Test de API:"
echo -e "     ${BLUE}curl http://localhost:8000/health${NC}"
echo ""
echo -e "${YELLOW}Happy coding! 🚀${NC}"
echo ""
