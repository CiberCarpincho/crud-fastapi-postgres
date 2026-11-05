# Build
FROM eclipse-temurin:21-jdk AS build
WORKDIR /app

COPY gradle ./gradle
COPY gradlew gradlew.bat settings.gradle build.gradle ./
RUN chmod +x gradlew

# Descarga las dependencias en una capa separada para aprovechar la cache de Docker.
RUN ./gradlew dependencies --no-daemon || true

COPY src ./src
RUN ./gradlew bootJar --no-daemon -x test \
    && cp "$(find build/libs -name '*.jar' ! -name '*-plain.jar' | head -n 1)" /app/app.jar

# Runtime
FROM eclipse-temurin:21-jre
WORKDIR /app

COPY --from=build /app/app.jar app.jar

EXPOSE 8085

ENTRYPOINT ["java", "-jar", "app.jar"]
