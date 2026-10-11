FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN --mount=type=secret,id=ca_bundle npm ci --cafile /run/secrets/ca_bundle
COPY . .
RUN npm run check && npm run build
CMD ["npm", "run", "dev"]
