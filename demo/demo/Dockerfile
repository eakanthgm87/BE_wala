FROM gradle:8-jdk17 AS builder
WORKDIR /app
COPY build.gradle* settings.gradle* gradlew* ./
COPY gradle gradle/
RUN ./gradlew dependencies --no-daemon -q 2>/dev/null || true
COPY . .
RUN ./gradlew bootJar --no-daemon -q -Porg.gradle.java.installations.auto-detect=false -Porg.gradle.java.installations.auto-download=false 2>/dev/null || ./gradlew jar --no-daemon -q -Porg.gradle.java.installations.auto-detect=false -Porg.gradle.java.installations.auto-download=false

FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=builder /app/build/libs/*.jar /app/app.jar
EXPOSE 8080
CMD ["java", "-jar", "/app/app.jar"]
