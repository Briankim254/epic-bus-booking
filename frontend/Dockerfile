# Build context: repository root (yarn workspace lockfile lives there)
FROM node:22-alpine

RUN corepack enable

WORKDIR /app

COPY package.json yarn.lock .yarnrc.yml ./
COPY frontend/package.json ./frontend/

RUN yarn install --immutable

COPY frontend ./frontend

WORKDIR /app/frontend

EXPOSE 5173

CMD ["yarn", "dev", "--host", "0.0.0.0"]
