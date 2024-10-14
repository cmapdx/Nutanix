# Updates Categories on VMs to add the missing AppType category

This python script will get a list of assigned categories and update to add the approriate AppType when missing.

With lots of applications there was a need to break the list into smaller groups.  The list of applications was split into 4 groups.  Each VM requires both AppType and the alphabet grouping to be picked up by a Flow security policy.  The AppType was missed when the VMs were being migrated.  This is a programatic fix to add the missing AppType category based on the grouping.