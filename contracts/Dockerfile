# Production Dockerfile for CampusOS Quai Network Smart Contracts
FROM node:20-alpine

WORKDIR /app
ENV NODE_ENV=production

RUN addgroup --system --gid 1002 hardhat && \
    adduser --system --uid 1002 hardhat

COPY package.json package-lock.json ./
RUN npm ci --include=dev

COPY . .
RUN chmod +x ./scripts/deploy-entrypoint.sh && \
    npx hardhat compile && \
    chown -R hardhat:hardhat /app

USER hardhat

ENTRYPOINT ["./scripts/deploy-entrypoint.sh"]
