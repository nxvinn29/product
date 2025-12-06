FROM node:18-alpine

WORKDIR /app

# Copy only frontend files

COPY frontend/package.json ./
RUN npm install

COPY frontend/ .

EXPOSE 3000
CMD ["npm", "run", "dev"]
