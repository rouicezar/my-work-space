// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "FormaAIPackagingPrototype",
    platforms: [.macOS(.v15)],
    products: [
        .library(name: "LifecycleContract", targets: ["LifecycleContract"]),
        .library(name: "RuntimeSecurity", targets: ["RuntimeSecurity"]),
        .library(name: "SupervisorProtocol", targets: ["SupervisorProtocol"]),
        .executable(name: "forma-ai-launcher", targets: ["FormaAILauncher"]),
        .executable(name: "FormaAIApp", targets: ["FormaAIApp"]),
    ],
    targets: [
        .target(name: "LifecycleContract"),
        .target(name: "RuntimeSecurity"),
        .target(name: "SupervisorProtocol"),
        .executableTarget(
            name: "FormaAILauncher",
            dependencies: ["LifecycleContract"]
        ),
        .executableTarget(
            name: "FormaAIApp",
            dependencies: ["LifecycleContract", "SupervisorProtocol", "RuntimeSecurity"]
        ),
        .testTarget(
            name: "LifecycleContractTests",
            dependencies: ["LifecycleContract"]
        ),
        .testTarget(
            name: "RuntimeSecurityTests",
            dependencies: ["RuntimeSecurity"]
        ),
        .testTarget(
            name: "SupervisorProtocolTests",
            dependencies: ["SupervisorProtocol", "RuntimeSecurity"]
        ),
        .testTarget(
            name: "FormaAIAppTests",
            dependencies: ["FormaAIApp"]
        ),
    ]
)
