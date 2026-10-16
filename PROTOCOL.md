# SLR pilot — reviewer instructions (apply exactly)

You are an independent reviewer in a Systematic Literature Review on software architectures for AIoT systems.
Work ONLY from the paper's real text. Try to read the FULL TEXT (use WebFetch on the DOI page, arXiv, MDPI, publisher
open-access page, Semantic Scholar, or the author's repository). If you cannot get the full text, use the abstract from
qgs_abstracts.json and set "full_text_read": false. Never guess facts that are not in the text; use "Not reported".

## Inclusion criteria (ALL must hold)
IC1 Proposes, describes or evaluates a software architecture, reference architecture, framework or design pattern for a system with both IoT and AI/ML components.
IC2 Places at least one part (data processing, inference or training) on the edge or fog (not cloud-only).
IC3 Describes the architecture in enough detail (e.g. a diagram + components) to say what its architecture is.
IC4 Peer-reviewed journal or conference paper, 2018 or later.
## Exclusion criteria (ANY excludes)
EC1 not English; EC2 secondary study (survey/SLR); EC3 <6 pages, poster, editorial, book, thesis; EC4 hardware/network-only with no software architecture;
EC5 AI algorithm only, no system architecture described; EC6 duplicate; EC7 full text unavailable (for the pilot, do NOT apply EC7; just flag it).

## Quality checklist (Yes=1, Partly=0.5, No=0)
Q1 aim clear; Q2 context described (domain, devices, scale); Q3 problem explained; Q4 related work compared;
Q5 architecture shown with diagram and components explained; Q6 target quality attributes explicit; Q7 clear which parts run on edge/fog/cloud;
Q8 design decisions/trade-offs explained; Q9 validated with measured results; Q10 reproducible (code, data or full setup available).

## Extraction fields (use these value sets; multiple allowed where it makes sense)
domain: Healthcare | Industry/IIoT | Smart city | Agriculture | Energy | Transport | Smart home | Generic | Other
contribution_type: Reference architecture | Concrete architecture | Framework | Design pattern | Platform
styles: Layered | Microservices | Service-oriented | Event-driven | Serverless | Edge-native/osmotic | Peer-to-peer | Hybrid | Not reported
communication: MQTT | AMQP | CoAP | HTTP/REST | gRPC | Kafka/event streaming | Other | Not reported
deployment_tech: free list (e.g. Docker, Kubernetes, K3s, AWS Greengrass, Azure IoT Edge) or "Not reported"
quality_attributes: Latency | Throughput | Scalability | Availability/Resilience | Security | Privacy | Explainability | Energy | Cost | Interoperability | Maintainability | Accuracy
privacy_approach: None | Encryption only (TLS) | Access control | Anonymisation | Differential privacy | Federated learning | Homomorphic encryption | Blockchain
explainability_approach: None | Inside the model only | Post-hoc (SHAP/LIME etc.) | Separate service in the architecture
inference_location: Device | Edge | Fog | Cloud (multiple allowed)
training_location: Device | Edge | Fog | Cloud | Federated | Not reported
allocation_strategy: Fixed at design time | Rule-based at runtime | Optimisation-based at runtime | Learning-based at runtime
validation_method: None | Example scenario | Simulation | Lab testbed | Real deployment | Formal proof
baseline: None | Monolith or cloud-only | Other architecture (name it)
code_available: Yes | No ; dataset_public: Yes | No | Not reported ; setup_fully_described: Yes | Partly | No

## Output: one JSON object per paper, in a JSON array, written with the Write tool to the file path you are given:
{"n":..,"doi":..,"full_text_read":true/false,"source_url":"..","decision":"include"|"exclude","criteria_failed":["IC2",...],
 "decision_reason":"one sentence","quality":{"Q1":1,...,"Q10":0},"quality_total":..,
 "extraction":{field: value or [values], ...},"evidence":{"styles":"short quote or section ref", "allocation_strategy":"...", "validation_method":"..."},
 "hard_to_decide":["fields that were ambiguous and why"]}
Work independently: do not look for or read other reviewers' files in this folder.
