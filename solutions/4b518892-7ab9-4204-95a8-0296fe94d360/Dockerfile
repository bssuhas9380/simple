FROM node:20-slim
WORKDIR /app
COPY . /app/
RUN if [ -f package.json ]; then npm install 2>&1; fi
CMD ["node", "server.js"]
