# ==================================
# FR: Dockerfile Frontend Next.js
# ==================================

FROM node:20-alpine

# FR: Définir le répertoire de travail
WORKDIR /app

# FR: Copier package.json et package-lock.json
COPY package*.json ./

# FR: Installer les dépendances
RUN npm ci

# FR: Copier le code source
COPY . .

# FR: Exposer le port
EXPOSE 3000

# FR: Variables d'environnement
ENV NODE_ENV=development

# FR: Commande de démarrage (development)
CMD ["npm", "run", "dev"]

# TODO (FR): Pour la production, utiliser le build multi-stage :
# FROM node:20-alpine AS builder
# WORKDIR /app
# COPY package*.json ./
# RUN npm ci
# COPY . .
# RUN npm run build
# 
# FROM node:20-alpine
# WORKDIR /app
# COPY --from=builder /app/public ./public
# COPY --from=builder /app/.next/standalone ./
# COPY --from=builder /app/.next/static ./.next/static
# EXPOSE 3000
# CMD ["node", "server.js"]

