# build env
FROM node:18
WORKDIR /app
COPY package*.json package-lock.json ./
RUN npm install --legacy-peer-deps
COPY . ./
RUN npm run build
CMD cp -r build result_build

