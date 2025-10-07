# Stage 1: Build and run the React application in development mode
FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Expose port 3000 for the React development server
EXPOSE 3000

# Start the React development server
CMD ["npm", "start"]
