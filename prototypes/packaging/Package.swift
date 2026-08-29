// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "MacAIWorkOSPackagingPrototype",
    platforms: [.macOS(.v15)],
    products: [
        .library(name: "LifecycleContract", targets: ["LifecycleContract"]),
        .library(name: "RuntimeSecurity", targets: ["RuntimeSecurity"]),
        .library(name: "SupervisorProtocol", targets: ["SupervisorProtocol"]),
        .executable(name: "mac-ai-work-os-launcher", targets: ["MacAIWorkOSLauncher"]),
        .executable(name: "MacAIWorkOSApp", targets: ["MacAIWorkOSApp"]),
    ],
    targets: [
        .target(name: "LifecycleContract"),
        .target(name: "RuntimeSecurity"),
        .target(name: "SupervisorProtocol"),
        .executableTarget(
            name: "MacAIWorkOSLauncher",
            dependencies: ["LifecycleContract"]
        ),
        .executableTarget(
            name: "MacAIWorkOSApp",
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
    ]
)
