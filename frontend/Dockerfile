# build env
FROM node:18
WORKDIR /app
COPY package*.json ./
RUN npm install -g npm@6
RUN npm install react-scripts@5.0.1
COPY . ./
RUN npm run build
CMD cp -r build result_build
