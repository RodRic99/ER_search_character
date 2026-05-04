FROM eclipse-temurin:17-jdk AS builder
WORKDIR /app

COPY gradlew gradlew.bat settings.gradle build.gradle gradle.properties ./
COPY gradle ./gradle
COPY src ./src
RUN chmod +x ./gradlew && ./gradlew bootJar

FROM eclipse-temurin:17-jre
WORKDIR /app

COPY --from=builder /app/build/libs/*.jar app.jar

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
