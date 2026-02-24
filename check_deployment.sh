#!/bin/bash
# Deployment Health Check Script
# Usage: ./check_deployment.sh

set -e

echo "======================================"
echo "Social Network API - Deployment Check"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if docker-compose is running
echo "1. Checking Docker Compose services..."
if docker compose ps | grep -q "social_network-api-1"; then
    echo -e "${GREEN}✓${NC} Docker Compose services are running"
else
    echo -e "${RED}✗${NC} Docker Compose services are not running"
    echo "Run: docker compose up -d"
    exit 1
fi
echo ""

# Check individual services
echo "2. Checking individual services..."
services=("postgres" "redis" "kafka" "zookeeper" "api")
for service in "${services[@]}"; do
    if docker compose ps | grep "social_network-${service}-1" | grep -q "Up"; then
        echo -e "${GREEN}✓${NC} ${service} is running"
    else
        echo -e "${RED}✗${NC} ${service} is not running"
    fi
done
echo ""

# Check API health endpoints
echo "3. Checking API health endpoints..."

# Liveness
liveness=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health/liveness 2>/dev/null || echo "000")
if [ "$liveness" = "200" ]; then
    echo -e "${GREEN}✓${NC} Liveness check passed (HTTP 200)"
else
    echo -e "${RED}✗${NC} Liveness check failed (HTTP ${liveness})"
fi

# Readiness
readiness=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health/readiness 2>/dev/null || echo "000")
if [ "$readiness" = "200" ]; then
    echo -e "${GREEN}✓${NC} Readiness check passed (HTTP 200)"
else
    echo -e "${RED}✗${NC} Readiness check failed (HTTP ${readiness})"
fi

# OpenAPI docs
docs=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null || echo "000")
if [ "$docs" = "200" ]; then
    echo -e "${GREEN}✓${NC} API documentation accessible (HTTP 200)"
else
    echo -e "${RED}✗${NC} API documentation not accessible (HTTP ${docs})"
fi
echo ""

# Check database migrations
echo "4. Checking database migrations..."
migration_output=$(docker compose exec -T api alembic current 2>&1 || echo "error")
if echo "$migration_output" | grep -q "202501010000"; then
    echo -e "${GREEN}✓${NC} Database migrations applied"
else
    echo -e "${YELLOW}⚠${NC} Migrations may not be applied. Run: docker compose exec api alembic upgrade head"
fi
echo ""

# Port information
echo "5. Service ports:"
echo "   - API:        http://localhost:8000"
echo "   - API Docs:   http://localhost:8000/docs"
echo "   - PostgreSQL: localhost:5432"
echo "   - Redis:      localhost:6380"
echo "   - Kafka:      localhost:9093"
echo "   - Zookeeper:  localhost:2181"
echo ""

# Summary
echo "======================================"
echo -e "${GREEN}✓ Deployment check complete!${NC}"
echo "======================================"
echo ""
echo "Next steps:"
echo "  - View logs:     docker compose logs -f api"
echo "  - Run tests:     make test-integration"
echo "  - Stop services: docker compose down"

