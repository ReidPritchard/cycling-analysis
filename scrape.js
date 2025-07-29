// // Stars
// document.querySelectorAll(".valeur-sportif")
// // Name
// document.querySelectorAll(".nom-sportif")
// // Team
// document.querySelectorAll(".club-sportif")
// // Position/Role
// document.querySelectorAll("#list-joueur .position")

// // Next page
// document.querySelector("button.mat-mdc-tooltip-trigger:nth-child(4)")

const scrapePage = () => {
    const names = document.querySelectorAll(".nom-sportif")
    const teams = document.querySelectorAll(".club-sportif")
    const positions = document.querySelectorAll("#list-joueur .position")
    const stars = document.querySelectorAll(".valeur-sportif")

    // remap rider name as key, team, position, stars as values
    const riders = []
    for (let i = 0; i < names.length; i++) {
        riders.push({
            name: names[i].textContent.trim(),
            team: teams[i].textContent.trim(),
            position: positions[i].textContent.trim(),
            stars: stars[i].textContent.trim()
        })
    }

    return riders
}


const main = async () => {
    const nextPage = document.querySelector("button.mat-mdc-tooltip-trigger:nth-child(4)")
    const riders = {}

    // Each page has 10 riders, there are 146 riders total (146 / 10 = 14.6 = 15 pages)
    let page = 1
    while (page <= 15) {
        console.log(`Scraping page ${page}/15`)
        const ridersOnPage = scrapePage()
        // Add the riders ([{name, team, position, stars}]) to the riders object
        ridersOnPage.forEach((rider) => {
            riders[rider.name] = rider
        })
        nextPage.click()

        // Wait for 1 second
        await new Promise(resolve => setTimeout(resolve, 1000))
        page++
    }
    console.log("Scraping complete")

    // Log the riders object as a json string
    // so it can be easily copied and saved to a file
    console.log(JSON.stringify(riders, null, 2))
}

main()