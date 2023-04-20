include {
  path = "../../../source/terragrunt/dns.hcl"
}

inputs = {
  perimeter_alb = {
    dev_test = "Public-DevTest-perimeter-alb"
    prod     = "Public-Prod-perimeter-alb"
  }
}
