# OTEL Logging Examples for Azure Application Insights

In this repo you'll find examples of how logging with OpenTelemetry (aka OTEL) and Azure can be setup.

This is extraction of knowledge collected since January 2022 with OpenCensus (soon deprecated; stop using this package!), transition to OTEL in January 2023 and building a bunch of utility monitoring and observability tools/functions/mechanisms for a fleet of over a dozen of services maintained and developed by a few people.

I hope you'll find this useful.

Consider this repo to be in constant development. There's not a lot of files currently, see them all, start with code then see images. Do not skip comments.

**PRs and Issues are welcome!** 

I'll do my best to share my expertise with y'all!


### Issues
- Open an issue if you're having a hard time setting up Application Insights or need any advice in this regard and be patient.
- Open an issue if you want to discuss ideas
- Open an issue if you don't agree with some of my statements regarding logging


### PRs aka "I know a better way!"
Show us! Open a PR with your implementation. We can work on it together. 


## Recognition

Thanks to:
- @tkutcher for original [issue](https://github.com/Azure/azure-functions-python-worker/issues/1319) 
- @dmillican-camillo for communicating that there is some confusion around OTEL logging being "unstable" and difficulties with finding examples
- @lzchen @jeremydvoss for their incredible job in OTEL and Azure community
