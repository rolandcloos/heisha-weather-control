#!/bin/bash
# Build script for Heisha Weather Prediction Control Add-On

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ADDON_NAME="heisha-weather-control"
VERSION=$(grep '"version"' config.json | cut -d'"' -f4)
ARCHITECTURES=("amd64" "aarch64" "armhf" "armv7" "i386")

echo -e "${BLUE}Building Heisha Weather Prediction Control Add-On v${VERSION}${NC}"

# Check dependencies
check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is required but not installed${NC}"
        exit 1
    fi
    
    if ! command -v docker buildx &> /dev/null; then
        echo -e "${RED}Docker buildx is required${NC}"
        exit 1
    fi
    
    # Check for Python3
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Python3 is required but not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Dependencies OK${NC}"
}

# Setup buildx
setup_buildx() {
    echo -e "${YELLOW}Setting up Docker Buildx...${NC}"
    
    # Create builder if it doesn't exist
    if ! docker buildx ls | grep -q "addon-builder"; then
        docker buildx create --name addon-builder --platform linux/amd64,linux/arm64,linux/arm/v7,linux/arm/v6,linux/386
    fi
    
    docker buildx use addon-builder
    echo -e "${GREEN}Buildx setup complete${NC}"
}

# Build for single architecture
build_arch() {
    local arch=$1
    echo -e "${YELLOW}Building for ${arch}...${NC}"
    
    # Map HA architectures to Docker platforms
    case $arch in
        "amd64")
            platform="linux/amd64"
            ;;
        "aarch64")
            platform="linux/arm64"
            ;;
        "armhf")
            platform="linux/arm/v6"
            ;;
        "armv7")
            platform="linux/arm/v7"
            ;;
        "i386")
            platform="linux/386"
            ;;
        *)
            echo -e "${RED}Unknown architecture: ${arch}${NC}"
            return 1
            ;;
    esac
    
    # Build the image
    docker buildx build \
        --platform ${platform} \
        --build-arg BUILD_FROM="ghcr.io/home-assistant/${arch}-base:3.18" \
        --build-arg BUILD_ARCH=${arch} \
        --build-arg BUILD_VERSION=${VERSION} \
        --tag ghcr.io/roland/${ADDON_NAME}:${VERSION}-${arch} \
        --tag ghcr.io/roland/${ADDON_NAME}:latest-${arch} \
        --load \
        .
    
    echo -e "${GREEN}Build complete for ${arch}${NC}"
}

# Build for all architectures
build_all() {
    echo -e "${YELLOW}Building for all architectures...${NC}"
    
    local platforms=""
    for arch in "${ARCHITECTURES[@]}"; do
        case $arch in
            "amd64") platforms="${platforms}linux/amd64," ;;
            "aarch64") platforms="${platforms}linux/arm64," ;;
            "armhf") platforms="${platforms}linux/arm/v6," ;;
            "armv7") platforms="${platforms}linux/arm/v7," ;;
            "i386") platforms="${platforms}linux/386," ;;
        esac
    done
    platforms=${platforms%,}  # Remove trailing comma
    
    docker buildx build \
        --platform ${platforms} \
        --build-arg BUILD_VERSION=${VERSION} \
        --tag ghcr.io/roland/${ADDON_NAME}:${VERSION} \
        --tag ghcr.io/roland/${ADDON_NAME}:latest \
        --push \
        .
    
    echo -e "${GREEN}Multi-architecture build complete${NC}"
}

# Run tests
run_tests() {
    echo -e "${YELLOW}Running tests...${NC}"
    
    if [ -f "requirements-test.txt" ]; then
        # Install test dependencies
        pip3 install -r requirements-test.txt
        
        # Run tests
        python3 -m pytest tests/ -v --cov=app --cov-report=html
        
        echo -e "${GREEN}Tests passed${NC}"
    else
        echo -e "${YELLOW}No test requirements found, skipping tests${NC}"
    fi
}

# Validate configuration
validate_config() {
    echo -e "${YELLOW}Validating configuration...${NC}"
    
    # Check required files
    required_files=("config.yaml" "config.json" "Dockerfile" "run.sh" "requirements.txt")
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            echo -e "${RED}Required file missing: ${file}${NC}"
            exit 1
        fi
    done
    
    # Validate JSON
    echo "Validating config.json..."
    if ! python3 -m json.tool config.json > /dev/null 2>&1; then
        echo -e "${RED}Invalid JSON in config.json${NC}"
        echo "JSON validation error details:"
        python3 -m json.tool config.json
        exit 1
    fi
    echo "config.json is valid"
    
    # Also validate config.yaml if it exists
    if [ -f "config.yaml" ]; then
        echo "config.yaml found (YAML validation would require PyYAML)"
    fi
    
    echo -e "${GREEN}Configuration valid${NC}"
}

# Test local build
test_local() {
    local arch=${1:-amd64}
    echo -e "${YELLOW}Testing local build for ${arch}...${NC}"
    
    # Build for local testing
    docker build \
        --build-arg BUILD_FROM="ghcr.io/home-assistant/${arch}-base:3.18" \
        --tag ${ADDON_NAME}:test \
        .
    
    # Run container with test environment
    echo -e "${YELLOW}Starting test container...${NC}"
    
    CONTAINER_ID=$(docker run --rm -d \
        --name ${ADDON_NAME}-test \
        -e MQTT_BROKER=test \
        -e MQTT_PORT=1883 \
        -e WEATHER_PROVIDER=openweathermap \
        -e WEATHER_API_KEY=test \
        -e LATITUDE=51.1657 \
        -e LONGITUDE=10.4515 \
        -e LOG_LEVEL=DEBUG \
        ${ADDON_NAME}:test)
    
    echo "Container started with ID: $CONTAINER_ID"
    
    # Wait and check logs
    sleep 10
    echo -e "${YELLOW}Container logs:${NC}"
    docker logs $CONTAINER_ID
    
    # Check if container is still running
    if docker ps | grep -q $CONTAINER_ID; then
        echo -e "${GREEN}Test container is running successfully${NC}"
        docker stop $CONTAINER_ID
    else
        echo -e "${RED}Test container failed to start properly${NC}"
        # Show exit code and logs for debugging
        echo "Container exit code:"
        docker ps -a | grep $CONTAINER_ID
        docker logs $CONTAINER_ID
        exit 1
    fi
}

# Clean up build artifacts
cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"
    
    # Remove test containers
    docker ps -a | grep ${ADDON_NAME} | awk '{print $1}' | xargs -r docker rm -f
    
    # Remove dangling images
    docker image prune -f
    
    echo -e "${GREEN}Cleanup complete${NC}"
}

# Main function
main() {
    case "${1:-all}" in
        "deps")
            check_dependencies
            ;;
        "validate")
            validate_config
            ;;
        "test")
            run_tests
            ;;
        "test-local")
            validate_config
            test_local ${2:-amd64}
            ;;
        "build")
            check_dependencies
            validate_config
            setup_buildx
            if [ -n "$2" ]; then
                build_arch $2
            else
                for arch in "${ARCHITECTURES[@]}"; do
                    build_arch $arch
                done
            fi
            ;;
        "build-all")
            check_dependencies
            validate_config
            setup_buildx
            build_all
            ;;
        "clean")
            cleanup
            ;;
        "all")
            check_dependencies
            validate_config
            run_tests
            setup_buildx
            test_local
            for arch in "${ARCHITECTURES[@]}"; do
                build_arch $arch
            done
            echo -e "${GREEN}Build complete for all architectures!${NC}"
            ;;
        *)
            echo "Usage: $0 {deps|validate|test|test-local [arch]|build [arch]|build-all|clean|all}"
            echo ""
            echo "Commands:"
            echo "  deps        - Check build dependencies"
            echo "  validate    - Validate configuration files"
            echo "  test        - Run unit tests"
            echo "  test-local  - Build and test locally"
            echo "  build       - Build for all architectures (or specific arch)"
            echo "  build-all   - Build multi-arch and push to registry"
            echo "  clean       - Clean up build artifacts"
            echo "  all         - Run full build pipeline (default)"
            echo ""
            echo "Supported architectures: ${ARCHITECTURES[*]}"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"