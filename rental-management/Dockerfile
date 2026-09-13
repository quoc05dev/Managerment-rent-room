# ===== BUILD STAGE =====
FROM maven:3.8-openjdk-11-slim AS build
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline -B
COPY src ./src
RUN mvn package -DskipTests -B

# ===== RUN STAGE =====
FROM openjdk:11-jre-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libreoffice-core && rm -rf /var/lib/apt/lists/*
COPY --from=build /app/target/*.jar app.jar
RUN mkdir -p /hdd/data/photographer/upload /hdd/data/photographer/tmp
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
