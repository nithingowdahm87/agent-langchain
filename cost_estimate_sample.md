
| Resource Type | Details | Estimated Monthly Cost |
|---|---|---|
| **Compute** | 3 Replicas x (0.5 vCPU, 1Gi RAM) -> AWS t3.small (~$20/mo) | ~$60.00 |
| **Storage** | 100Gi gp3 EBS volume | ~$10.00 |
| **LoadBalancer** | 1 AWS ALB | ~$18.00 |

**Total Estimated Monthly Cost**: ~$88.00 - $100.00

**Recommendations**:
- Use Spot instances for backend replicas to save ~50%.
- Review PVC size; 100Gi might be overprovisioned.
