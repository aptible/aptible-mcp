DEPROVISION_APP = """
jobs:
  deprovision-app:
    name: Deprovision Review App and Databases
    runs-on: ubuntu-24.04
    steps:
      - name: Install aptible CLI
        run: |
          PKG="$(mktemp)"
          curl -fsSL "${{ env.CLI_URL }}" > "$PKG"
          sudo dpkg -i "$PKG"
          rm "$PKG"
          aptible login --email "${{ secrets.APTIBLE_ROBOT_USERNAME }}" --password "${{ secrets.APTIBLE_ROBOT_PASSWORD }}"

      - name: Deprovision app
        run: |
          aptible apps:deprovision --app ${{ vars.APTIBLE_APP_NAME }} --environment ${{ vars.APTIBLE_ENVIRONMENT_NAME }} || exit 0
"""

PROVISION_APP = """
jobs:
  deprovision-app:
    name: Deprovision Review App and Databases
    runs-on: ubuntu-24.04
    steps:
      - name: Install aptible CLI
        run: |
          PKG="$(mktemp)"
          curl -fsSL "${{ env.CLI_URL }}" > "$PKG"
          sudo dpkg -i "$PKG"
          rm "$PKG"
          aptible login --email "${{ secrets.APTIBLE_ROBOT_USERNAME }}" --password "${{ secrets.APTIBLE_ROBOT_PASSWORD }}"
      - name: Find or create API App
        run: aptible apps:create --environment ${{ vars.APTIBLE_ENVIRONMENT_NAME }} ${{ vars.APTIBLE_APP_NAME }} || exit 0
"""

CONFIGURE_APP = """
jobs:
  deprovision-app:
    name: Deprovision Review App and Databases
    runs-on: ubuntu-24.04
    steps:
      - name: Install aptible CLI
        run: |
          PKG="$(mktemp)"
          curl -fsSL "${{ env.CLI_URL }}" > "$PKG"
          sudo dpkg -i "$PKG"
          rm "$PKG"
          aptible login --email "${{ secrets.APTIBLE_ROBOT_USERNAME }}" --password "${{ secrets.APTIBLE_ROBOT_PASSWORD }}"
      - name: Configure app
        run: |
          aptible config:set --environment ${{ vars.APTIBLE_ENVIRONMENT_NAME }} --app ${{ env.APTIBLE_API_APP_NAME }} \
            DATABASE_URL="${{ env.PG_DATABASE_URL }}" \
            CELERY_BROKER_URL="${{ env.REDIS_DATABASE_URL }}" \
            FORCE_SSL=true \
            SECRET_KEY=${{ secrets.SECRET_KEY }} \
            FIELD_ENCRYPTION_KEYS=${{ secrets.FIELD_ENCRYPTION_KEYS }} \
            IDLE_TIMEOUT=90
"""

DEPROVISION_DATABASE = """
jobs:
  deprovision-app:
    name: Deprovision Review App and Databases
    runs-on: ubuntu-24.04
    steps:
      - name: Install aptible CLI
        run: |
          PKG="$(mktemp)"
          curl -fsSL "${{ env.CLI_URL }}" > "$PKG"
          sudo dpkg -i "$PKG"
          rm "$PKG"
          aptible login --email "${{ secrets.APTIBLE_ROBOT_USERNAME }}" --password "${{ secrets.APTIBLE_ROBOT_PASSWORD }}"
      - name: Deprovision database
        run: |
          aptible db:deprovision ${{ vars.DATABASE_NAME }} --environment ${{ vars.APTIBLE_ENVIRONMENT_NAME }} || exit 0
"""

PROVISION_DATABASE = """
jobs:
  build-publish-deploy:
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Install aptible CLI
        run: |
          PKG="$(mktemp)"
          curl -fsSL "${{ env.CLI_URL }}" > "$PKG"
          sudo dpkg -i "$PKG"
          rm "$PKG"
          aptible login --email "${{ secrets.APTIBLE_ROBOT_USERNAME }}" --password "${{ secrets.APTIBLE_ROBOT_PASSWORD }}"
      - name: Create PostgreSQL database
        run: |
          aptible db:create "${{ vars.DATABASE_NAME }}" --environment ${{ vars.APTIBLE_ENVIRONMENT_NAME }} --type postgresql || true
      - name: Set PostgreSQL database env var
        run: |
          PG_DATABASE_URL=$(APTIBLE_OUTPUT_FORMAT=json aptible db:list --environment ${{ vars.APTIBLE_ENVIRONMENT_NAME }} | jq -r '.[] | select(.handle=="${{ vars.DATABASE_NAME }}")| .connection_url')
          echo "PG_DATABASE_URL=$PG_DATABASE_URL" >> $GITHUB_ENV || exit 0
"""

RESTORE_FROM_BACKUP = """
jobs:
  build-publish-deploy:
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Install aptible CLI
        run: |
          PKG="$(mktemp)"
          curl -fsSL "${{ env.CLI_URL }}" > "$PKG"
          sudo dpkg -i "$PKG"
          rm "$PKG"
          aptible login --email "${{ secrets.APTIBLE_ROBOT_USERNAME }}" --password "${{ secrets.APTIBLE_ROBOT_PASSWORD }}"

      - name: Get most recent backup
        run: |
          BACKUP_ID=$(aptible backup:list ${{ vars.DATABASE_NAME }} --environment ${{ vars.APTIBLE_ENVIRONMENT_NAME }} | head -n 1 | awk -F ':' '{print $1}')
          aptible backup:restore ${BACKUP_ID} --handle ${{ vars.DATABASE_NAME }}-restore
"""

PROVISION_ENDPOINT = """
jobs:
  deprovision-app:
    name: Deprovision Review App and Databases
    runs-on: ubuntu-24.04
    steps:
      - name: Install aptible CLI
        run: |
          PKG="$(mktemp)"
          curl -fsSL "${{ env.CLI_URL }}" > "$PKG"
          sudo dpkg -i "$PKG"
          rm "$PKG"
          aptible login --email "${{ secrets.APTIBLE_ROBOT_USERNAME }}" --password "${{ secrets.APTIBLE_ROBOT_PASSWORD }}"
      - name: Create app endpoint
        run: |
          aptible endpoints:https:create --environment ${{ vars.APTIBLE_ENVIRONMENT_NAME }} --app ${{ vars.APTIBLE_APP_NAME }} --default-domain "cmd" --ip-whitelist ${{ vars.SAFE_IP_1 }} ${{ vars.SAFE_IP_2 }}  || exit 0
"""

BUILD_PUBLISH_DEPLOY = """
jobs:
  build-publish-deploy:
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Install aptible CLI
        run: |
          PKG="$(mktemp)"
          curl -fsSL "${{ env.CLI_URL }}" > "$PKG"
          sudo dpkg -i "$PKG"
          rm "$PKG"
          aptible login --email "${{ secrets.APTIBLE_ROBOT_USERNAME }}" --password "${{ secrets.APTIBLE_ROBOT_PASSWORD }}"

      - name: Log in to the Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Extract metadata (tags, labels) for Docker
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix=sha-
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
      - name: Deploy to Aptible
        uses: aptible/aptible-deploy-action@v4
        with:
          username: ${{ secrets.APTIBLE_ROBOT_USERNAME }}
          password: ${{ secrets.APTIBLE_ROBOT_PASSWORD }}
          environment: ${{ vars.APTIBLE_ENVIRONMENT_NAME }}
          app: ${{ vars.APTIBLE_APP_NAME }}
          docker_img: ghcr.io/${{ github.repository }}:${{ github.ref_name }}
          private_registry_username: ${{ github.actor }}
          private_registry_password: ${{ secrets.GITHUB_TOKEN }}
"""
