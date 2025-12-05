FROM node:18-alpine

WORKDIR /app

# Copy only frontend files
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --silent

COPY frontend/ .

EXPOSE 3000
CMD ["npm", "run", "dev"]
